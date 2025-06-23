import subprocess
import os
import json

from PIL import Image, ImageDraw, ImageFont

def create_thumbnail(text, output_path, size=(640, 360)):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

    # Draw text on image
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
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


FFPROBE_PATH = r"D:/icons/code/bin/ffprobe.exe"
FFMPEG_PATH = r"D:/icons/code/bin/ffmpeg.exe"

def split_video_fast(input_path, clip_length=90):
    if not os.path.exists(input_path):
        print("Video file not found.")
        return

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

    file_name, ext = os.path.splitext(os.path.basename(input_path))
    output_dir = f"{file_name} Clips"
    os.makedirs(output_dir, exist_ok=True)

    i = 0
    start = 0
    while start < duration:
        part_name = f"{file_name} Part {i+1}"
        output_file = os.path.join(output_dir, f"{part_name}{ext}")
        thumbnail_path = os.path.join(output_dir, f"{part_name}_thumb.jpg")
        final_output = os.path.join(output_dir, f"{part_name}_with_thumb{ext}")

        # Step 1: Split video
        split_cmd = [
            FFMPEG_PATH, '-ss', str(start), '-i', input_path,
            '-t', str(clip_length),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            output_file, '-y'
        ]
        subprocess.run(split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 2: Create thumbnail
        create_thumbnail(f"{part_name}", thumbnail_path)

        # Step 3: Add thumbnail to video
        add_thumbnail_to_video(output_file, thumbnail_path, final_output)

        # Optionally delete raw split and thumbnail
        os.remove(output_file)
        # os.remove(thumbnail_path)

        start += clip_length
        i += 1

    print(f"Video split into {i} parts with thumbnails in '{output_dir}'")


# Example usage
split_video_fast(r"D:/icons/Freddy (2022).mp4", clip_length=90)