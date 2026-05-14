<div align="center">
  <a href="https://pypi.org/project/extra-roformers" target="_blank"><img src="https://img.shields.io/pypi/v/extra-roformers?label=PyPI%20Version&color=limegreen" /></a>
  <a href="https://pypi.org/project/extra-roformers" target="_blank"><img src="https://img.shields.io/pypi/pyversions/extra-roformers?color=limegreen" /></a>
  <a href="https://github.com/mohammadmansour200/extra-roformers/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/pypi/l/extra-roformers?color=limegreen" /></a>
  <a href="https://pepy.tech/project/extra-roformers" target="_blank"><img src="https://static.pepy.tech/badge/extra-roformers" /></a>
  <a href="https://baseet.netlify.app/ai" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" /></a>
</div>

`extra-roformers`: Extended [audio-separator](https://github.com/nomadkaraoke/python-audio-separator/) with yt-dlp media downloading and Video
Music removal

## Features

- 🎧 **Vocal isolation** using Mel-Band RoFormer model
- 📥 **Media download** from URLs (e.g., YouTube) using `yt-dlp`
- 📁 Works with both **audio** and **video** files
- ✅ Local + remote (URL) input support

## Get started

*Make sure you have [ffmpeg](https://www.ffmpeg.org/download.html) installed.*

```bash
sudo apt install ffmpeg
```

Download package:
> Requires Python 3.10+

```bash
pip install extra-roformers
```

## Usage

```bash
from extra_roformers.separate import extra_separator

extra_separator(
    files=[
        "https://www.youtube.com/watch?v=123",
        "local_audio.mp3"
    ],
    download_format="audio",   # or "video"
    quality="medium",     # "low", "medium", "high"
    output_dir="outputs"
)

```
