import os
import zipfile
import shutil
from PIL import Image

# 🔧 Set your zip file path here
INPUT_ZIP = r"C:/Users/91701/Downloads/images.zip"

# Output paths
BASE_DIR = os.path.dirname(INPUT_ZIP)
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_images")
OUTPUT_DIR = os.path.join(BASE_DIR, "compressed_images")
OUTPUT_ZIP = os.path.join(BASE_DIR, "optimized_images.zip")
COMPRESSION_QUALITY = 85
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png')

# Step 1: Extract zip file
with zipfile.ZipFile(INPUT_ZIP, 'r') as zip_ref:
    zip_ref.extractall(EXTRACT_DIR)

# Step 2: Duplicate structure
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
shutil.copytree(EXTRACT_DIR, OUTPUT_DIR)

# Step 3: Resize and compress images
def process_image(path, quality=85):
    try:
        with Image.open(path) as img:
            ext = os.path.splitext(path)[1].lower()
            is_png = ext == '.png'

            # Resize if width ≥ 1500px
            if img.width >= 1500:
                aspect_ratio = img.height / img.width
                new_width = 900
                new_height = int(new_width * aspect_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                print(f"🔻 Resized: {path} ({img.width}x{img.height})")

            if is_png:
                # Keep transparency and save as PNG
                img.save(path, optimize=True)
            else:
                # Convert to RGB if needed and save as JPEG
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(path, format='JPEG', optimize=True, quality=quality)

            print(f"✔ Processed: {path}")
    except Exception as e:
        print(f"✘ Skipped: {path} ({e})")

for root, _, files in os.walk(OUTPUT_DIR):
    for file in files:
        if file.lower().endswith(ALLOWED_EXTENSIONS):
            process_image(os.path.join(root, file), COMPRESSION_QUALITY)

# Step 4: Zip compressed folder
shutil.make_archive(OUTPUT_ZIP.replace(".zip", ""), 'zip', OUTPUT_DIR)

# Step 5: Final report
final_size = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
print(f"\n✅ Done! Optimized zip saved to:\n{OUTPUT_ZIP}\nFinal size: {final_size:.2f} MB")
