import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from queue import Empty, Queue

MODEL = "htdemucs"
PROGRESS = re.compile(r"^\s*(\d+)%")
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def separate(source, destination, report):
    import imageio_ffmpeg

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".vocalsplit-", dir=destination) as temporary:
        work = Path(temporary)
        report("正在解码音频…")
        decoded = work / "input.wav"
        result = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-i", str(source),
             "-map", "0:a:0", "-ac", "2", "-ar", "44100", "-c:a", "pcm_f32le", str(decoded)],
            capture_output=True, encoding="utf-8", errors="replace", creationflags=FLAGS,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "无法解码音频。")

        report("正在加载模型，首次使用会下载模型…")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        with subprocess.Popen(
            [sys.executable, "-m", "demucs", "-n", MODEL, "-d", "cpu",
             "--two-stems", "vocals", "-o", str(work), str(decoded)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8",
            errors="replace", env=env, creationflags=FLAGS,
        ) as process:
            tail = []
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                tail = (tail + [line])[-12:]
                progress = PROGRESS.match(line)
                if progress:
                    report(f"模型下载或分离进度 {progress.group(1)}%")
                elif line.startswith("Separating"):
                    report("正在分离人声与伴奏…")
            if process.wait():
                raise RuntimeError("\n".join(tail) or "分离引擎运行失败。")

        stems = work / MODEL / "input"
        for name in ("vocals.wav", "no_vocals.wav"):
            if not (stems / name).is_file() or (stems / name).stat().st_size <= 44:
                raise RuntimeError("分离引擎未生成完整的音轨。")
        (stems / "no_vocals.wav").rename(stems / "instrumental.wav")
        # Each job gets its own output folder, including runs of the same song.
        for index in range(1, 10000):
            suffix = "" if index == 1 else f"_{index}"
            output = destination / f"{source.stem[:80]}_stems{suffix}"
            try:
                stems.rename(output)
            except FileExistsError:
                continue
            return output
        raise RuntimeError("同名结果文件夹过多，请换一个输出位置。")


if os.environ.get("VOCALSPLIT_OFFLINE") == "1":
    from offline import separate


def main():
    root = tk.Tk()
    root.title("人声与伴奏分离 · 离线立体声模式" if os.getenv("VOCALSPLIT_OFFLINE") else "人声与伴奏分离")
    root.minsize(640, 340)
    root.configure(background="#edf2f2")
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#edf2f2")
    style.configure("TLabel", background="#edf2f2", foreground="#203635",
                    font=("Microsoft YaHei UI", 10))
    style.configure("Title.TLabel", font=("Microsoft YaHei UI", 22, "bold"))
    style.configure("Go.TButton", font=("Microsoft YaHei UI", 11, "bold"), padding=(16, 8))
    style.map("Go.TButton", background=[("disabled", "#a5b2b2"), ("active", "#176959"),
                                        ("!disabled", "#205d53")],
              foreground=[("!disabled", "white")])

    panel = ttk.Frame(root, padding=30)
    panel.pack(fill="both", expand=True)
    panel.columnconfigure(0, weight=1)
    ttk.Label(panel, text="人声与伴奏分离", style="Title.TLabel").grid(row=0, sticky="w")
    source = tk.StringVar()
    destination = tk.StringVar(value=str(Path(__file__).resolve().parent / "results"))
    status = tk.StringVar(value="选择歌曲后即可开始。输出为两条 WAV 音轨。")
    events = Queue()
    output = None
    busy = False

    def choose(field, dialog):
        selection = dialog(parent=root)
        if selection:
            field.set(selection)

    for row, label, value, dialog in (
        (1, "音频文件", source, lambda **kw: filedialog.askopenfilename(
            filetypes=[("音频文件", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.opus *.wma"),
                       ("所有文件", "*.*")], **kw)),
        (3, "输出目录", destination, filedialog.askdirectory),
    ):
        ttk.Label(panel, text=label).grid(row=row, sticky="w", pady=(14, 3))
        ttk.Entry(panel, textvariable=value).grid(row=row + 1, column=0, sticky="ew", ipady=4)
        ttk.Button(panel, text="浏览…", command=lambda v=value, d=dialog: choose(v, d)).grid(
            row=row + 1, column=1, padx=(8, 0), sticky="ew")

    def start():
        nonlocal busy, output
        song = Path(source.get().strip())
        target = destination.get().strip()
        if not song.is_file() or not target:
            messagebox.showwarning("请选择文件", "请选择一个音频文件和输出目录。", parent=root)
            return
        busy = True
        output = None
        go.configure(state="disabled")
        open_result.configure(state="disabled")
        status.set("正在启动分离引擎…")

        def run():
            try:
                result = separate(song.resolve(), Path(target).expanduser().resolve(),
                                  lambda message: events.put(("status", message)))
                events.put(("done", result))
            except Exception as error:
                events.put(("error", str(error)))

        threading.Thread(target=run, daemon=True).start()

    def poll():
        nonlocal busy, output
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == "status":
                    status.set(value)
                    continue
                busy = False
                go.configure(state="normal")
                if kind == "done":
                    output = value
                    status.set("分离完成。已生成 vocals.wav 和 instrumental.wav。")
                    open_result.configure(state="normal")
                else:
                    status.set("分离失败，请查看错误详情。")
                    messagebox.showerror("分离失败", value, parent=root)
        except Empty:
            pass
        root.after(150, poll)

    def open_folder():
        try:
            os.startfile(output)
        except OSError as error:
            messagebox.showerror("无法打开结果", str(error), parent=root)

    go = ttk.Button(panel, text="开始分离", style="Go.TButton", command=start)
    go.grid(row=5, column=0, pady=(20, 0), sticky="w")
    open_result = ttk.Button(panel, text="打开结果", state="disabled", command=open_folder)
    open_result.grid(row=5, column=1, pady=(20, 0))
    ttk.Label(panel, textvariable=status, wraplength=550).grid(
        row=6, columnspan=2, pady=(14, 0), sticky="w")

    def close():
        if busy:
            messagebox.showinfo("正在分离", "当前歌曲仍在处理，请等待任务结束。", parent=root)
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.after(150, poll)
    root.mainloop()


if __name__ == "__main__":
    main()

