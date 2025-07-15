import subprocess
import os
import json
import argparse
import tempfile
from PIL import Image, ImageDraw, ImageFont

def hms_to_seconds(hms):
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s

FFPROBE_PATH = r"bin/ffprobe.exe"
FFMPEG_PATH = r"bin/ffmpeg.exe"

def get_music_files_from_directory(music_dir):
    supported_exts = ('.mp3', '.wav', '.aac', '.m4a')
    return [
        os.path.join(music_dir, f)
        for f in os.listdir(music_dir)
        if f.lower().endswith(supported_exts)
    ]

def get_audio_duration(file_path):
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
    if not music_paths:
        print("No music files found in the directory.")
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

def replace_video_audio(video_path, music_path, output_path):
    cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        '[1:a]volume=0.05[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=3[a]',
        '-map', '0:v',
        '-map', '[a]',
        '-c:v', 'copy',
        '-shortest',
        output_path, '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("Audio replacement failed:", result.stderr.decode())

def create_thumbnail(text, output_path, size=(640, 360)):
    img = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill="white", font=font)
    img.save(output_path)

def add_thumbnail_to_video(video_path, thumbnail_path, output_path):
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

def split_video_fast(input_path, music_folder, clip_length=90, trim_start="00:00:00", trim_end=None):
    if not os.path.exists(input_path):
        print("Video file not found.")
        return

    original_file_name, original_ext = os.path.splitext(os.path.basename(input_path))

    trim_start_sec = hms_to_seconds(trim_start)
    trim_end_sec = hms_to_seconds(trim_end) if trim_end else None
    trim_duration = trim_end_sec - trim_start_sec if trim_end_sec else None

    trimmed_video_path = f"{original_file_name}_trimmed{original_ext}"
    trim_cmd = [
        FFMPEG_PATH, "-ss", trim_start,
        "-i", input_path
    ]
    if trim_duration:
        trim_cmd += ["-t", str(trim_duration)]
    trim_cmd += ["-c", "copy", trimmed_video_path, "-y"]
    subprocess.run(trim_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input_path = trimmed_video_path

    result = subprocess.run([
        FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        input_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    try:
        result_json = json.loads(result.stdout)
        duration = float(result_json['format']['duration'])
    except (KeyError, ValueError, json.JSONDecodeError):
        print("Failed to retrieve video duration. Check ffprobe path or input file.")
        return

    music_files = get_music_files_from_directory(music_folder)
    music_dir_name = os.path.basename(os.path.normpath(music_folder)).replace(" ", "_")
    combined_music = f"{music_dir_name}_combined.mp3"
    combined_music = combine_and_loop_music(music_files, duration, combined_music)

    if not combined_music:
        print("No valid music to overlay. Exiting.")
        return

    audio_added_video = f"{original_file_name}_with_music{original_ext}"
    replace_video_audio(input_path, combined_music, audio_added_video)
    input_path = audio_added_video

    output_dir = f"{original_file_name} Clips"
    os.makedirs(output_dir, exist_ok=True)

    i = 0
    start = 0
    while start < duration:
        part_name = f"{original_file_name} Part {i+1}"
        output_file = os.path.join(output_dir, f"{part_name}{original_ext}")
        thumbnail_path = os.path.join(output_dir, f"{part_name}_thumb.jpg")
        final_output = os.path.join(output_dir, f"{part_name}_with_thumb{original_ext}")

        split_cmd = [
            FFMPEG_PATH, '-ss', str(start), '-i', input_path,
            '-t', str(clip_length),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            output_file, '-y'
        ]
        subprocess.run(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        create_thumbnail(part_name, thumbnail_path)
        add_thumbnail_to_video(output_file, thumbnail_path, final_output)

        os.remove(output_file)
        # os.remove(thumbnail_path)  # optionally keep

        start += clip_length
        i += 1

    print(f"Video split into {i} parts with thumbnails in '{output_dir}'")

    os.remove(combined_music)
    os.remove(audio_added_video)
    os.remove(trimmed_video_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Split video with music and thumbnails")
    parser.add_argument('video_path', help='Path to the input video file')
    parser.add_argument('music_folder', help='Path to the folder with background music files')
    parser.add_argument('--clip_length', type=int, default=90, help='Length of each clip in seconds')
    parser.add_argument('--trim_start', default="00:00:00", help='Start time for trimming (HH:MM:SS)')
    parser.add_argument('--trim_end', default=None, help='End time for trimming (HH:MM:SS)')

    args = parser.parse_args()
    split_video_fast(
        args.video_path,
        args.music_folder,
        clip_length=args.clip_length,
        trim_start=args.trim_start,
        trim_end=args.trim_end
    )
