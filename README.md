# ClipSync

Version: **1.1.0-sun**

English:
Synchronize canvas preview image from .clip file to .png file in blender

日本語:
.clipファイルからcanvasのプレビュー画像を.pngファイルに同期するアドオン

## Demo Link (x.com)

https://x.com/arthur484_/status/1846780897724715502

## Download

English:
This is a volunteer project.  If you find it useful, please consider supporting my work by purchasing something from my shop. I would greatly appreciate it, and it will help me continue to improve ClipSync!

日本語:
ボランティア開発のため、あ～さ～のboothを見てくれたら、
跳ねて喜びぶよ～! 今後のClipSyncのバージョンアップのモチベーションにするよ!

[Blender addon](https://github.com/arthur-vr/ClipSync/releases)

[Desktop App](https://arthur484.booth.pm/items/8609124)

## How to invoke

![Search](./images/demo_search.png)

English:
- Install the addon
- press F3 and type `clipsync`

日本語:
- アドオンをインストール
- f3を押してclipsyncと検索

## Panel Description


### .clip mode
![Panel](./images/demo_panel.png)


English:
- clip slot 1-5: set the path of the clip under Users/*, only the clip file that exists will be synchronized
- use parent folder: use parent folder or not. If you want to specify a directory other than the directory of the .clip file, set this to true
- parent folder: set the path of the parent folder
- suffix: set the suffix of the file name (example: v2)
- sync interval: set the interval of the sync(seconds)
- Document: open the document in the web browser
- Stop: stop the sync
- OK: save the settings and execute the sync, after that, the sync will be started automatically, .png file will be generated in the same directory as the .clip file, please set the png file as the texture


日本語:
- clip slot 1-5: Users/*以下のclipファイルのパスを設定。存在しているclipファイルのみが同期される
- use parent folder: 親フォルダを使用するかどうか。.clipファイルと同じディレクトリ以外を指定可能
- parent folder: 親フォルダのパスを設定
- suffix: ファイル名の末尾に追加する文字列を設定 (例: v2)
- sync interval: 同期間隔を設定(秒)
- Document: ドキュメントをウェブブラウザで開く
- Stop: 同期を停止
- OK: 同期が開始され、.clipファイルと同じディレクトリに.pngファイルが生成されるので、それをテクスチャとして設定してください


### window capture mode

![Panel](./images/demo_window_capture.png)

English:
- Get the capture software on Booth: https://arthur484.booth.pm/items/8609124
- Press "Get Sync ON Projects" to sync the projects whose sync is turned ON in the desktop app.
- Turn on the checkbox and press OK, then a texture with that name will be synchronized. Use that image in your material.

日本語:
- https://arthur484.booth.pm/items/8609124 Boothでキャプチャ用ソフトを取得します
- 同期ONプロジェクトを取得(Get Sync ON Projects)を押すと、デスクトップアプリで同期がONになっているプロジェクト同期します。
- チェックボックスをOnにしてOKをおすとその名前でtextureが同期されるようになるので、その画像をマテリアルで使用します。


## Differences from AutoSync (frequently asked questions)

English:
- AutoSync can update supported image formats like PNG,PSD, but it doesn't support .clip files.
- AutoSync updates all images, which can be resource-intensive if you have many images. ClipSync only updates the specified image, making it lightweight.
- It intentionally uses only basic Python packages to ensure compatibility with a wide range of Blender versions.
- ClipSync is launched only by f3 search, and does not invade the UI.

日本語:
- AutoSyncはPNG,PSD等の対応画像を更新できるが、.clipファイルは更新できない
- AutoSyncはすべての画像を更新するため、画像が多いと重くなる可能性があるが、ClipSyncでは指定した一つの画像のみが更新されるので軽量である
- あえて、基本的なpythonパッケージのみを使用することで、幅広いバージョンのblenderでも動作するようにしている
- ClipSyncはf3検索からのみ起動され、UIを侵食しない


## Q&A

### English:
#### Image quality is poor when using 4k images
##### Window Capture mode has no such limitation, so even 4k images can be updated in real time.

#### Real-time update is not performed in .clip mode
##### This addon monitors the modification time of the .clip file, so when the modification time of the .clip file changes, the .png file is updated. In the demo video, ctrl+s is assigned to a button on the pen tablet to reflect the changes.
In Window Capture mode, it works in real time without saving.

### 日本語:
#### 4k画像だと画質が悪くなる
##### Window Captureのほうだと制限がないので4kでもリアルタイム更新できます。

#### .clipモードの場合はリアルタイムに更新されない
##### .clipファイルの更新日時を監視しているので、.clipファイルの更新日時が変わると、.pngファイルが更新されます。 デモの動画では、液タブのボタンにctrl+sを設定して、押して反映させています。
Window Captureモードであれば、セーブをしなくてもリアルタイムで動きます。
