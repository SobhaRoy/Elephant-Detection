import os
import shutil
import random
from pathlib import Path
from ultralytics import YOLO

# Paths
SOURCE_DIR = Path("dataset/sri-lankan-wild-elephant-dataset")
TARGET_DIR = Path("dataset/processed")
ELEPHANT_CLASS_ID = 20  # COCO class for elephant

# Initialize base detector
model = YOLO("yolov8n.pt")

# Create standard YOLO directory structure
for split in ["train", "val"]:
    (TARGET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

# Find all images
all_images = list(SOURCE_DIR.glob("*.jpg")) + list(SOURCE_DIR.glob("*.png"))
print(f"[*] Found {len(all_images)} total source images.")

# Sample 1,200 images for efficient transfer learning
random.seed(42)
sampled = random.sample(all_images, min(1200, len(all_images)))
valid_pairs = []

print("[*] Running automated bounding box annotation...")
for i, img_path in enumerate(sampled):
    results = model(str(img_path), verbose=False)[0]
    boxes = [b for b in results.boxes if int(b.cls[0]) == ELEPHANT_CLASS_ID and float(b.conf[0]) >= 0.40]

    if not boxes:
        continue

    # Prepare standard YOLO label lines: <class> <x_center> <y_center> <width> <height>
    h, w = results.orig_shape
    label_lines = []
    for b in boxes:
        xywhn = b.xywhn[0].tolist()
        label_lines.append(f"0 {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}")

    valid_pairs.append((img_path, label_lines))

    if (i + 1) % 150 == 0:
        print(f"    Processed {i + 1}/{len(sampled)} images...")

print(f"[+] Successfully auto-labeled {len(valid_pairs)} high-confidence images.")

# Split 80% train, 20% validation
random.shuffle(valid_pairs)
split_idx = int(len(valid_pairs) * 0.8)
splits = {"train": valid_pairs[:split_idx], "val": valid_pairs[split_idx:]}

for split_name, items in splits.items():
    for img_p, lines in items:
        dest_img = TARGET_DIR / "images" / split_name / img_p.name
        dest_lbl = TARGET_DIR / "labels" / split_name / f"{img_p.stem}.txt"

        shutil.copy(img_p, dest_img)
        dest_lbl.write_text("\n".join(lines), encoding="utf-8")

# Generate data.yaml
yaml_content = f"""path: {TARGET_DIR.resolve().as_posix()}
train: images/train
val: images/val

names:
  0: elephant
"""
Path("data.yaml").write_text(yaml_content, encoding="utf-8")
print("[+] Created data.yaml and formatted YOLO dataset in dataset/processed/")
