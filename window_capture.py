import array
import http.client
import queue
import re
import struct
import threading
import time
import urllib.parse

import bpy

try:
    import numpy as np
except ImportError:
    np = None


MAGIC = b"CBRG"
HEADER_SIZE = 20
TILE_MAGIC = b"CBT1"
TILE_HEADER_SIZE = 26
TILE_RECORD_SIZE = 8
_STOP_EVENTS = []
LATENCY_REPORT_SECONDS = 2.0


def _fetch_frame(connection, path, since=None):
    """Fetch pixels and their authoritative dimensions from canvas-bridge."""
    request_path = path
    if since is not None:
        request_path += ("&" if "?" in request_path else "?") + f"since={since}"
    connection.request("GET", request_path, headers={"Connection": "keep-alive"})
    response = connection.getresponse()
    payload = response.read()
    if response.status != 200:
        raise ConnectionError(
            f"ClipSync frame HTTP {response.status}: {response.reason}"
        )
    if len(payload) < HEADER_SIZE or payload[:4] not in {MAGIC, TILE_MAGIC}:
        raise ValueError("invalid ClipSync window capture frame")
    width, height, sequence = struct.unpack_from("<IIQ", payload, 4)
    if payload[:4] == MAGIC:
        pixels = payload[HEADER_SIZE:]
        if len(pixels) != width * height * 4:
            raise ValueError("incomplete ClipSync window capture frame")
        return width, height, sequence, pixels, None, len(payload)

    if len(payload) < TILE_HEADER_SIZE:
        raise ValueError("incomplete ClipSync tile frame")
    tile_size, tile_count = struct.unpack_from("<HI", payload, HEADER_SIZE)
    if tile_size <= 0:
        raise ValueError("invalid ClipSync tile size")
    offset = TILE_HEADER_SIZE
    tiles = []
    view = memoryview(payload)
    for _ in range(tile_count):
        if offset + TILE_RECORD_SIZE > len(payload):
            raise ValueError("incomplete ClipSync tile record")
        x, y, tile_width, tile_height = struct.unpack_from("<HHHH", payload, offset)
        offset += TILE_RECORD_SIZE
        if (
            tile_width <= 0
            or tile_height <= 0
            or x + tile_width > width
            or y + tile_height > height
        ):
            raise ValueError("invalid ClipSync tile bounds")
        byte_count = tile_width * tile_height * 4
        end = offset + byte_count
        if end > len(payload):
            raise ValueError("incomplete ClipSync tile pixels")
        tiles.append((x, y, tile_width, tile_height, view[offset:end]))
        offset = end
    if offset != len(payload):
        raise ValueError("unexpected trailing ClipSync tile data")
    return width, height, sequence, None, tiles, len(payload)


def image_name_for_project(project_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", project_id).strip("_") or "project"
    return f"ClipSync_Window_{safe}"


def _rgba_float_pixels(raw, output=None):
    if np is not None:
        source = np.frombuffer(raw, dtype=np.uint8)
        if output is None or output.size != source.size:
            output = np.empty(source.size, dtype=np.float32)
        np.multiply(source, 1.0 / 255.0, out=output, casting="unsafe")
        return output
    return array.array("f", (channel / 255.0 for channel in raw))


def _apply_tile_pixels(output, width, height, tiles):
    """Patch bottom-up RGBA8 tiles into the reusable full float buffer."""
    if np is not None:
        target = output.reshape(height, width, 4)
        for x, y, tile_width, tile_height, raw in tiles:
            source = np.frombuffer(raw, dtype=np.uint8).reshape(
                tile_height, tile_width, 4
            )
            np.multiply(
                source,
                1.0 / 255.0,
                out=target[y:y + tile_height, x:x + tile_width],
                casting="unsafe",
            )
        return output

    for x, y, tile_width, tile_height, raw in tiles:
        for row in range(tile_height):
            source_start = row * tile_width * 4
            target_start = ((y + row) * width + x) * 4
            for index in range(tile_width * 4):
                output[target_start + index] = raw[source_start + index] / 255.0
    return output


def stop_window_captures():
    """Stop worker threads; called before starting a new set or on Stop."""
    while _STOP_EVENTS:
        _STOP_EVENTS.pop().set()


def _tag_image_redraw():
    # Image datablocks update immediately, but explicitly tag editor areas so
    # an unfocused Blender window does not wait for the next user interaction.
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {"IMAGE_EDITOR", "VIEW_3D", "NODE_EDITOR"}:
                area.tag_redraw()


def _refresh_material_consumers(image):
    """Tag the Image itself; image.update() already invalidates its pixels."""
    try:
        image.update_tag()
    except Exception:
        pass


def start_window_capture(base_url, project_id, fps):
    endpoint = f"{base_url.rstrip('/')}/frame/{project_id}/rgba"
    parsed_endpoint = urllib.parse.urlsplit(endpoint)
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.hostname:
        raise ValueError(f"invalid ClipSync Window Capture URL: {base_url}")
    connection_type = (
        http.client.HTTPSConnection
        if parsed_endpoint.scheme == "https"
        else http.client.HTTPConnection
    )
    endpoint_port = parsed_endpoint.port or (
        443 if parsed_endpoint.scheme == "https" else 80
    )
    endpoint_path = parsed_endpoint.path or "/"
    if parsed_endpoint.query:
        endpoint_path += f"?{parsed_endpoint.query}"
    image_name = image_name_for_project(project_id)
    frames = queue.Queue(maxsize=1)
    stop_event = threading.Event()
    applied_lock = threading.Lock()
    applied_sequence = [None]
    fetch_interval = max(1.0 / 60.0, 1.0 / max(1, fps))
    apply_poll_seconds = max(1.0 / 60.0, 0.5 / max(1, fps))
    _STOP_EVENTS.append(stop_event)

    def worker():
        connection = None
        next_fetch_at = time.perf_counter()
        while not stop_event.is_set():
            try:
                if connection is None:
                    connection = connection_type(
                        parsed_endpoint.hostname,
                        endpoint_port,
                        timeout=1.0,
                    )
                with applied_lock:
                    since = applied_sequence[0]
                fetch_started = time.perf_counter()
                frame = _fetch_frame(connection, endpoint_path, since=since)
                fetch_ms = (time.perf_counter() - fetch_started) * 1000.0
                received_at = time.perf_counter()
                try:
                    frames.get_nowait()
                except queue.Empty:
                    pass
                try:
                    frames.put_nowait((*frame, fetch_ms, received_at))
                except queue.Full:
                    pass
            except Exception as exc:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception:
                        pass
                    connection = None
                print(f"[ClipSync Window Capture] {exc}")
            next_fetch_at += fetch_interval
            now = time.perf_counter()
            if next_fetch_at < now - fetch_interval:
                next_fetch_at = now
            stop_event.wait(max(0.0, next_fetch_at - now))
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    threading.Thread(
        target=worker,
        name=f"ClipSync Window Capture {project_id}",
        daemon=True,
    ).start()

    state = {
        "last_sequence": None,
        "report_at": time.perf_counter(),
        "count": 0,
        "fetch_ms": 0.0,
        "queue_ms": 0.0,
        "convert_ms": 0.0,
        "upload_ms": 0.0,
        "gpu_ms": 0.0,
        "e2e_ms": 0.0,
        "e2e_max_ms": 0.0,
        "wire_bytes": 0,
        "full_frames": 0,
        "delta_frames": 0,
        "empty_frames": 0,
        "pixel_buffer": None,
        "buffer_width": 0,
        "buffer_height": 0,
    }

    def record_latency(
        fetch_ms, queue_ms, convert_ms, upload_ms, gpu_ms, e2e_ms,
        wire_bytes, frame_kind,
    ):
        state["count"] += 1
        for key, value in (
            ("fetch_ms", fetch_ms),
            ("queue_ms", queue_ms),
            ("convert_ms", convert_ms),
            ("upload_ms", upload_ms),
            ("gpu_ms", gpu_ms),
            ("e2e_ms", e2e_ms),
        ):
            state[key] += value
        state["wire_bytes"] += wire_bytes
        state[f"{frame_kind}_frames"] += 1
        state["e2e_max_ms"] = max(state["e2e_max_ms"], e2e_ms)
        now = time.perf_counter()
        if now - state["report_at"] < LATENCY_REPORT_SECONDS:
            return
        count = max(1, state["count"])
        print(
            "[ClipSync Latency] "
            f"project={project_id} frames={count} "
            f"fetch={state['fetch_ms'] / count:.1f}ms "
            f"queue={state['queue_ms'] / count:.1f}ms "
            f"convert={state['convert_ms'] / count:.1f}ms "
            f"upload={state['upload_ms'] / count:.1f}ms "
            f"gpu={state['gpu_ms'] / count:.1f}ms "
            f"e2e={state['e2e_ms'] / count:.1f}ms "
            f"max={state['e2e_max_ms']:.1f}ms "
            f"wire={state['wire_bytes'] / count / 1024.0:.1f}KiB "
            f"full/delta/empty={state['full_frames']}/"
            f"{state['delta_frames']}/{state['empty_frames']} "
            f"numpy={'on' if np is not None else 'off'}"
        )
        for key in (
            "count", "fetch_ms", "queue_ms", "convert_ms", "upload_ms",
            "gpu_ms", "e2e_ms", "e2e_max_ms", "wire_bytes",
            "full_frames", "delta_frames", "empty_frames",
        ):
            state[key] = 0
        state["report_at"] = now

    def timer_func():
        if not getattr(bpy.types.Scene, "cs_is_loop", False) or stop_event.is_set():
            return None
        try:
            (
                width, height, sequence, raw, tiles, wire_bytes,
                fetch_ms, received_at,
            ) = frames.get_nowait()
            if state["last_sequence"] != sequence:
                queue_ms = (time.perf_counter() - received_at) * 1000.0
                image = bpy.data.images.get(image_name)
                is_full = raw is not None
                buffer_matches = (
                    state["pixel_buffer"] is not None
                    and state["buffer_width"] == width
                    and state["buffer_height"] == height
                )
                if not is_full and (
                    not buffer_matches
                    or image is None
                    or tuple(image.size) != (width, height)
                ):
                    # A delta is only useful on top of the exact frame Blender
                    # last applied. Ask the next worker iteration for CBRG.
                    with applied_lock:
                        applied_sequence[0] = None
                    state["last_sequence"] = None
                    state["pixel_buffer"] = None
                    return apply_poll_seconds

                if is_full:
                    if image is None:
                        image = bpy.data.images.new(
                            image_name, width=width, height=height
                        )
                    elif tuple(image.size) != (width, height):
                        image.scale(width, height)

                convert_started = time.perf_counter()
                if is_full:
                    values = _rgba_float_pixels(raw, state["pixel_buffer"])
                    state["pixel_buffer"] = values
                    state["buffer_width"] = width
                    state["buffer_height"] = height
                    frame_kind = "full"
                elif tiles:
                    values = _apply_tile_pixels(
                        state["pixel_buffer"], width, height, tiles
                    )
                    frame_kind = "delta"
                else:
                    values = None
                    frame_kind = "empty"
                convert_ms = (time.perf_counter() - convert_started) * 1000.0
                upload_ms = 0.0
                gpu_ms = 0.0
                if values is not None:
                    upload_started = time.perf_counter()
                    image.pixels.foreach_set(values)
                    image.update()
                    upload_ms = (time.perf_counter() - upload_started) * 1000.0
                    gpu_started = time.perf_counter()
                    _refresh_material_consumers(image)
                    _tag_image_redraw()
                    gpu_ms = (time.perf_counter() - gpu_started) * 1000.0
                state["last_sequence"] = sequence
                with applied_lock:
                    applied_sequence[0] = sequence
                e2e_ms = max(0.0, time.time() * 1000.0 - sequence)
                record_latency(
                    fetch_ms, queue_ms, convert_ms, upload_ms, gpu_ms, e2e_ms,
                    wire_bytes, frame_kind,
                )
        except queue.Empty:
            pass
        except Exception as exc:
            print(f"[ClipSync Window Capture] {exc}")
        return apply_poll_seconds

    bpy.app.timers.register(timer_func, first_interval=0.1, persistent=True)
