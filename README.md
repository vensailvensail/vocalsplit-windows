# VocalSplit · 人声与伴奏分离

在 Windows 本机将一首歌拆成两条 WAV 音轨。默认使用 Demucs 的 htdemucs 模型在 CPU 上处理，无需独立显卡。界面支持 MP3、WAV、FLAC、M4A 等常见音频格式。

## 下载与安装

1. 安装 **Python 3.11 的 Windows 64 位版本**，保留 Tcl/Tk 和 Python Launcher，并勾选 **Add python.exe to PATH**。安装器提供的 Python 3.11.9 可用于本工具。[Python 3.11.9 官方下载页](https://www.python.org/downloads/release/python-3119/)
2. 点击 **[下载 VocalSplit（ZIP）](https://github.com/vensailvensail/vocalsplit-windows/archive/refs/heads/main.zip)**，或在仓库首页选择 **Code → Download ZIP**。
3. 右键 ZIP，选择「全部解压」。打开包含 `Start.bat` 的文件夹，双击 `Start.bat` 启动 AI 模式。首次启动会创建 `.venv` 并下载 PyTorch CPU 版、Demucs 等依赖，请保持命令窗口打开。
4. 在中文界面选择音频，确认输出目录，点击「开始分离」。**第一次分离还需要联网下载模型**。启动脚本将模型缓存在 `cache/torch`，模型就绪后可离线使用。

## 查看结果

点击「打开结果」。默认输出位置是工具目录中的 `results/<歌曲名>_stems/`。每次处理会新建结果目录，里面有两条音轨。

| 文件 | 用途 |
| --- | --- |
| `vocals.wav` | 单独试听或编辑人声 |
| `instrumental.wav` | 试听或使用分离出的伴奏 |

## 轻量立体声模式

双击 `Start-Offline.bat` 可使用 FFmpeg 根据立体声的中央声像估算人声。首次启动需联网安装 imageio-ffmpeg，之后可断网使用，无需下载 AI 模型。这个模式适合人声居中的立体声录音，居中的乐器也可能进入人声音轨。对于单声道或混音复杂的歌曲，优先使用 `Start.bat`。

## 常见问题

- **找不到 Python 或安装 PyTorch 失败**。在新打开的终端运行 `py -3.11 -V` 或 `python --version`，确认已安装 64 位 Python 3.11，然后重新双击启动脚本。
- **第一次启动或分离较慢**。启动时需要下载安装包，第一次分离还要下载模型。后续分离速度主要取决于歌曲时长和 CPU 性能。

项目源码采用 [MIT 许可证](LICENSE)。[Demucs](https://github.com/facebookresearch/demucs)、[PyTorch](https://github.com/pytorch/pytorch) 和 [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) 等第三方组件单独安装，适用各自的许可。
