import subprocess
import os
import json
import argparse
import tempfile
from PIL import Image, ImageDraw, ImageFont
import re


def hms_to_seconds(hms):
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


FFPROBE_PATH = r"bin/ffprobe.exe"
FFMPEG_PATH = r"bin/ffmpeg.exe"


def get_music_files_from_directory(music_dir):
    print(f"Scanning music directory: {music_dir}")
    supported_exts = ('.mp3', '.wav', '.aac', '.m4a')
    return [
        os.path.join(music_dir, f)
        for f in os.listdir(music_dir)
        if f.lower().endswith(supported_exts)
    ]


def get_audio_duration(file_path):
    print(f"Getting audio duration for: {file_path}")
    result = subprocess.run([
        FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        return float(result.stdout.strip())
    except:
        return 0


def combine_and_loop_music(music_paths, total_duration, output_audio_path):
    print(f"Combining music files: {music_paths} for total duration: {total_duration} seconds")
    if not music_paths:
        return None

    looped_list = []
    accumulated_duration = 0
    music_index = 0

    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt', encoding='utf-8') as temp_file:
        while accumulated_duration < total_duration:
            music_path = music_paths[music_index % len(music_paths)]
            duration = get_audio_duration(music_path)
            looped_list.append(f"file '{os.path.abspath(music_path)}'")
            accumulated_duration += duration
            music_index += 1

        temp_file.write('\n'.join(looped_list))
        concat_list_path = temp_file.name

    concat_cmd = [
        FFMPEG_PATH, '-f', 'concat', '-safe', '0', '-i', concat_list_path,
        '-c', 'copy', output_audio_path, '-y'
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.remove(concat_list_path)
    return output_audio_path


def replace_video_audio(video_path, music_path, output_path, bg_volume):
    print(f"Replacing audio in {video_path} with {music_path} at volume {bg_volume}")
    cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        f'[1:a]volume={bg_volume}[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=3[a]',
        '-map', '0:v',
        '-map', '[a]',
        '-c:v', 'copy',
        '-shortest',
        output_path, '-y'
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def parse_style_arg(style_str):
    print(f"Parsing style string: {style_str}")
    result = {}
    if not style_str:
        return result
    tokens = re.findall(r'-([a-z_]+)-\s+([^\-]+)', style_str)
    for key, value in tokens:
        result[key] = value.strip()
    print(f"Parsed style result: {result}")
    return result


def create_thumbnail(text, output_path, size, font_settings):
    print(f"Creating thumbnail with text: '{text}' at {output_path} with size {size} and font settings {font_settings}")
    bg_color = font_settings.get("bg_color", "0x000000").replace("0x", "#")
    text_color = font_settings.get("color", "0xFFFFFF").replace("0x", "#")
    font_size = int(font_settings.get("size", 40))
    font_family = font_settings.get("family", "arial.ttf")

    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_family, font_size)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill=text_color, font=font)
    img.save(output_path)


def add_thumbnail_to_video(video_path, thumbnail_path, output_path):
    print(f"Adding thumbnail {thumbnail_path} to video {video_path} as attached picture")
    cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-i', thumbnail_path,
        '-map', '0',
        '-map', '1',
        '-c', 'copy',
        '-disposition:v:1', 'attached_pic',
        output_path,
        '-y'
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_drawtext_filter(top_text, bottom_text, top_font, bottom_font):
    print(f"Building drawtext filter for top: '{top_text}' and bottom: '{bottom_text}'")
    filters = []
    duration = 5

    def text_filter(text, y_pos, font):
        if not text:
            return None
        color = font.get("color", "0xFFFFFFFF").replace("0x", "#")
        size = font.get("size", "24")
        family = font.get("family", "arial.ttf")
        return (
            f"drawtext=text='{text}':fontfile='{family}':fontsize={size}:fontcolor={color}:"
            f"x=(w-text_w)/2:y={y_pos}:enable='lt(t\,{duration})'"
        )

    if top_text:
        filters.append(text_filter(top_text, 20, top_font))
    if bottom_text:
        filters.append(text_filter(bottom_text, "h-text_h-20", bottom_font))

    print(f"Generated drawtext filters: {filters}")
    return ",".join(filter(None, filters))


def get_video_resolution(video_path):
    print(f"Getting video resolution for: {video_path}")
    cmd = [
        FFPROBE_PATH, '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = json.loads(result.stdout)
    w = info['streams'][0]['width']
    h = info['streams'][0]['height']
    return (w, h)


def split_video_fast(args):
    print("Starting video split process...")
    input_path = args.input
    if not os.path.exists(input_path):
        print("Video file not found.")
        return

    os.makedirs(args.output_folder, exist_ok=True)

    original_file_name, original_ext = os.path.splitext(os.path.basename(input_path))

    trim_start_sec = hms_to_seconds(args.trim_start)
    trim_end_sec = hms_to_seconds(args.trim_end) if args.trim_end else None
    trim_duration = trim_end_sec - trim_start_sec if trim_end_sec else None

    trimmed_video_path = os.path.join(args.output_folder, f"{original_file_name}_trimmed{original_ext}")
    trim_cmd = [FFMPEG_PATH, "-ss", args.trim_start, "-i", input_path]
    if trim_duration:
        trim_cmd += ["-t", str(trim_duration)]
    trim_cmd += ["-c", "copy", trimmed_video_path, "-y"]
    
    print(f"Trimming video: {trimmed_video_path}")
    subprocess.run(trim_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input_path = trimmed_video_path

    print(f"Analyzing video duration for: {input_path}")
    result = subprocess.run([
        FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        input_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    try:
        duration = float(json.loads(result.stdout)['format']['duration'])
    except:
        print("Failed to retrieve duration.")
        return

    music_generated = None
    if args.music_folder and os.path.exists(args.music_folder):
        music_files = get_music_files_from_directory(args.music_folder)
        if music_files:
            combined_music_path = os.path.join(args.output_folder, f"{args.music_file_name or 'combined_music'}.mp3")
            music_generated = combine_and_loop_music(music_files, duration, combined_music_path)

            if music_generated:
                audio_added_video = os.path.join(args.output_folder, f"{original_file_name}_with_music{original_ext}")
                replace_video_audio(input_path, music_generated, audio_added_video, args.bg_volume)
                input_path = audio_added_video

    resolution = get_video_resolution(input_path)
    thumbnail_font = parse_style_arg(args.thumbnail_font)
    letterbox_settings = parse_style_arg(args.letterbox_setting)
    letterbox_top_font = parse_style_arg(args.letterbox_top_font)
    letterbox_bottom_font = parse_style_arg(args.letterbox_bottom_font)

    i = 0
    start = 0
    generated_files = []

    while start < duration:
        part_num = i + 1
        video_name = args.video_naming_convention.replace("..part", str(part_num))
        thumbnail_name = args.thumbnail_naming_convention.replace("..part", str(part_num))

        video_file = os.path.join(args.output_folder, f"{video_name}{original_ext}")
        thumb_path = os.path.join(args.output_folder, f"{thumbnail_name}.jpg")
        final_output = os.path.join(args.output_folder, f"{video_name}_with_thumb{original_ext}")

        top_text = letterbox_settings.get("top", "").replace("..part", str(part_num)).replace("..input", original_file_name)
        bottom_text = letterbox_settings.get("bottom", "").replace("..part", str(part_num)).replace("..input", original_file_name)
        drawtext_filter = build_drawtext_filter(top_text, bottom_text, letterbox_top_font, letterbox_bottom_font)

        vf_filters = [f"transpose={args.video_transpose}"] if args.video_transpose is not None else []
        if drawtext_filter:
            vf_filters.append(drawtext_filter)

        split_cmd = [
            FFMPEG_PATH, '-ss', str(start), '-i', input_path, '-t', str(args.clip_length),
            '-vf', ",".join(vf_filters),
            '-c:a', 'copy', '-avoid_negative_ts', 'make_zero', video_file, '-y'
        ]
        
        print(f"Splitting video: {video_file}")
        subprocess.run(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        create_thumbnail(video_name, thumb_path, resolution, thumbnail_font)
        add_thumbnail_to_video(video_file, thumb_path, final_output)

        generated_files += [video_file, thumb_path, final_output]

        start += args.clip_length
        i += 1

    print(f"Video split into {i} parts.")

    if os.path.exists(trimmed_video_path) and args.video_naming_convention:
        os.remove(trimmed_video_path)
    if music_generated and not args.music_file_name:
        os.remove(music_generated)
    if not args.video_naming_convention:
        for file in generated_files:
            if os.path.exists(file):
                os.remove(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split and process videos with optional music, thumbnails, and letterbox text overlays.")
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--music_folder', help='Path to folder with background music')
    parser.add_argument('--bg_volume', type=float, default=0.05, help='Volume level for background music')
    parser.add_argument('--output_folder', required=True, help='Path to output folder')
    parser.add_argument('--clip_length', type=int, default=90, help='Length of each video part in seconds')
    parser.add_argument('--trim_start', default="00:00:00", help='Start time to trim video (HH:MM:SS)')
    parser.add_argument('--trim_end', help='End time to trim video (HH:MM:SS)')
    parser.add_argument('--video_naming_convention', default="clip ..part", help='Naming pattern for output video parts, use ..part')
    parser.add_argument('--thumbnail_naming_convention', default="thumb ..part", help='Naming pattern for thumbnail files, use ..part')
    parser.add_argument('--music_file_name', help='Name of combined music file without extension')
    parser.add_argument('--letterbox_setting', help='Overlay text settings like "-top- text1 -bottom- text2"')
    parser.add_argument('--thumbnail_font', help='Font settings for thumbnails like "-family- arial.ttf -size- 42 -color- 0xFF000000 -bg_color- 0xFFFFFFFF"')
    parser.add_argument('--letterbox_top_font', help='Font settings for top letterbox text (same format as thumbnail_font)')
    parser.add_argument('--letterbox_bottom_font', help='Font settings for bottom letterbox text (same format as thumbnail_font)')
    parser.add_argument('--video_transpose', type=int, help='Set transpose filter value (0=90°CW+vflip, 1=90°CW, 2=90°CCW, 3=90°CCW+vflip)')

    args = parser.parse_args()
    split_video_fast(args)
