# 🎬 Video Splitter & Enhancer

A powerful Python tool to trim, split, and enhance videos by adding optional background music, styled letterbox text overlays, and thumbnails. Built using **FFmpeg** and **Pillow**, this script is ideal for content creators automating video editing workflows.

---

## ✨ Features

- 🔪 Trim videos by start and end times
- ✂️ Split videos into multiple clips of fixed duration
- 🎶 Add background music from a folder and loop it to fit video duration
- 🔊 Adjust background music volume
- 📝 Add top and bottom letterbox-style text overlays
- 🖼 Generate and embed styled thumbnails for each video clip
- ↪️ Optionally rotate (transpose) the video

---

## 🚀 Usage

Run the script from the command line:

```bash
python script.py --input input.mp4 --output_folder output --clip_length 60 --music_folder music --letterbox_setting "-top- My Clip -bottom- Part ..part"
```

---

## 🧾 Arguments

| Argument | Type | Required | Description |
|---------|------|----------|-------------|
| `--input` | str | ✅ Yes | Path to the input video file |
| `--output_folder` | str | ✅ Yes | Directory where output clips and thumbnails will be saved |
| `--clip_length` | int | No (default: `90`) | Duration (in seconds) of each split video part |
| `--trim_start` | str | No (default: `00:00:00`) | Start time for trimming the video (format: `HH:MM:SS`) |
| `--trim_end` | str | No | End time for trimming (format: `HH:MM:SS`). If not provided, uses full video duration |
| `--music_folder` | str | No | Folder path containing background music files (`.mp3`, `.wav`, `.aac`, `.m4a`) |
| `--music_file_name` | str | No | Filename for the combined music file (without extension). Default is `combined_music.mp3` |
| `--bg_volume` | float | No (default: `0.05`) | Background music volume (0.0 to 1.0) |
| `--video_naming_convention` | str | No (default: `"clip ..part"`) | Output naming template for video clips. Use `..part` as placeholder for part number |
| `--thumbnail_naming_convention` | str | No (default: `"thumb ..part"`) | Output naming template for thumbnails. Use `..part` as placeholder |
| `--thumbnail_font` | str | No | Font settings for thumbnail. Format: `-family- arial.ttf -size- 42 -color- 0xFF000000 -bg_color- 0xFFFFFFFF` |
| `--letterbox_setting` | str | No | Text overlay content. Format: `-top- ..input -bottom- Part ..part` |
| `--letterbox_top_font` | str | No | Font style for top overlay text (same format as `--thumbnail_font`) |
| `--letterbox_bottom_font` | str | No | Font style for bottom overlay text (same format as `--thumbnail_font`) |
| `--video_transpose` | int | No | Rotate the video using FFmpeg’s transpose filter. Options: `0=90°CW+vflip`, `1=90°CW`, `2=90°CCW`, `3=90°CCW+vflip` |

---

## 🛠 Requirements

- Python 3.6+
- [FFmpeg](https://ffmpeg.org/download.html) (with `ffmpeg` and `ffprobe` in the `bin/` directory)
- [Pillow](https://pillow.readthedocs.io/en/stable/) for image manipulation

Install Pillow with:
```bash
pip install Pillow
```

---

## 📂 Output

For each clip, the script generates:

- A trimmed and optionally transposed video part with optional overlays
- A thumbnail image (JPEG)
- A final video file with the thumbnail embedded as metadata

---

## 🧪 Example

```bash
python script.py \
  --input myvideo.mp4 \
  --output_folder clips \
  --clip_length 60 \
  --trim_start 00:00:10 \
  --trim_end 00:05:00 \
  --music_folder bgm \
  --bg_volume 0.08 \
  --letterbox_setting "-top- ..input -bottom- Part ..part" \
  --thumbnail_font "-family- arial.ttf -size- 42 -color- 0xFFFFFFFF -bg_color- 0x000000" \
  --letterbox_top_font "-family- arial.ttf -size- 32 -color- 0xFFFFFF" \
  --letterbox_bottom_font "-family- arial.ttf -size- 28 -color- 0xCCCCCC" \
  --video_transpose 1
```