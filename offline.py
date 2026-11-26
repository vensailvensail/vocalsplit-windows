import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import imageio_ffmpeg


def separate(source, destination, report):
    destination.mkdir(parents=True, exist_ok=True)
    report("正在提取居中人声并生成伴奏…")
    with TemporaryDirectory(dir=destination) as tmp:
        stems = Path(tmp) / "tracks"
        stems.mkdir()
        graph = (
            "aformat=channel_layouts=stereo,dialoguenhance=original=1:enhance=0.5,"
            "asplit=2[v][a];[v]pan=mono|c0=FC,highpass=f=100,lowpass=f=9000,"
            "asplit=2[voice][subtract];[a]pan=stereo|c0=FL|c1=FR[lr];"
            "[subtract]pan=stereo|c0=-1*c0|c1=-1*c0[neg];"
            "[lr][neg]amix=inputs=2:normalize=0[backing]"
        )
        result = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-nostdin", "-loglevel", "error", "-i",
             str(source), "-filter_complex", "[0:a:0]" + graph,
             "-map", "[voice]", "-c:a", "pcm_s24le", str(stems / "vocals.wav"),
             "-map", "[backing]", "-c:a", "pcm_s24le", str(stems / "instrumental.wav")],
            capture_output=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            output = destination / f"{source.stem[:80]}_stems{suffix}"
            try:
                stems.rename(output)
                return output
            except FileExistsError:
                index += 1