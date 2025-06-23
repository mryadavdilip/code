import subprocess
import os
import json

FFPROBE_PATH = r"D:/icons/code/bin/ffprobe.exe"
FFMPEG_PATH = r"D:/icons/code/bin/ffmpeg.exe"

def split_video_fast(input_path, clip_length=90):
    if not os.path.exists(input_path):
        print("Video file not found.")
        return

    # Use full path to ffprobe
    result = subprocess.run([
        FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        input_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    duration = float(json.loads(result.stdout)['format']['duration'])

    file_name, ext = os.path.splitext(os.path.basename(input_path))
    output_dir = f"{file_name}_clips"
    os.makedirs(output_dir, exist_ok=True)

    i = 0
    start = 0
    while start < duration:
        output_file = os.path.join(output_dir, f"{file_name}_part_{i+1}{ext}")
        cmd = [
            FFMPEG_PATH, '-ss', str(start), '-i', input_path,
            '-t', str(clip_length),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            output_file, '-y'
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start += clip_length
        i += 1

    print(f"Video split into {i} parts in '{output_dir}'")

# Example usage
split_video_fast(r"D:/icons/freddy copy.mkv", clip_length=90)
