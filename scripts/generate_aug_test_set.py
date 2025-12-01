# generate_augmented_test_set.py

import os
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

SOURCE_DIR = Path("landmarks")
TARGET_DIR = Path("test_augmented")
AUG_PER_IMAGE = 4   # how many augmented copies per original

TARGET_DIR.mkdir(exist_ok=True)

def random_augment(img: Image.Image) -> Image.Image:
    # slightly stronger rotation
    angle = random.uniform(-35, 35)
    img = img.rotate(angle, expand=True, fillcolor=(0, 0, 0))

    # more aggressive random crop (55–100% area)
    w, h = img.size
    scale = random.uniform(0.55, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    left = random.randint(0, max(0, w - new_w))
    top = random.randint(0, max(0, h - new_h))
    img = img.crop((left, top, left + new_w, top + new_h))
    img = img.resize((w, h))

    # brightness + contrast (a bit wider range)
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.45, 1.6))
    img = ImageEnhance.Contrast(img).enhance(random.uniform(0.45, 1.6))

    # blur fairly often
    if random.random() < 0.75:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(2.5, 5.0)))

    # noise: mostly moderate, sometimes strong
    if random.random() < 0.9:
        arr = np.array(img).astype("float32")
        # 80% of the time: std ~22, 20% of the time: std ~35
        if random.random() < 0.8:
            noise_std = 22
        else:
            noise_std = 35
        noise = np.random.normal(0, noise_std, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype("uint8")
        img = Image.fromarray(arr)

    return img



def main():
    for class_name in sorted(d for d in os.listdir(SOURCE_DIR)
                             if (SOURCE_DIR / d).is_dir()):
        src_class_dir = SOURCE_DIR / class_name
        dst_class_dir = TARGET_DIR / class_name
        dst_class_dir.mkdir(parents=True, exist_ok=True)

        for fname in os.listdir(src_class_dir):
            src_path = src_class_dir / fname
            if not src_path.is_file():
                continue

            try:
                img = Image.open(src_path).convert("RGB")
            except Exception as e:
                print(f"Skipping {src_path}: {e}")
                continue

            stem = src_path.stem
            for i in range(AUG_PER_IMAGE):
                aug_img = random_augment(img)
                out_name = f"{stem}_aug{i+1}.jpg"
                out_path = dst_class_dir / out_name
                aug_img.save(out_path, quality=85)
                print(f"Saved {out_path}")

if __name__ == "__main__":
    main()
