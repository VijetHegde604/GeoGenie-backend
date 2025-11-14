from icrawler.builtin import GoogleImageCrawler
import math
import os

# List of famous landmarks (you can edit or add more)
landmarks = [
    "Eiffel Tower",
    "Taj Mahal",
    "Statue of Liberty",
    "Great Wall of China",
    "Machu Picchu",
    "Colosseum Rome",
    "Christ the Redeemer Rio",
    "Pyramids of Giza",
    "Sydney Opera House",
    "Big Ben London"
]

# Total number of images you want
TOTAL_IMAGES = 1000

# Images per landmark (rounded)
images_per_landmark = math.ceil(TOTAL_IMAGES / len(landmarks))

base_dir = "landmarks"
os.makedirs(base_dir, exist_ok=True)

for landmark in landmarks:
    print(f"📸 Downloading {images_per_landmark} images of {landmark}...")
    folder = os.path.join(base_dir, landmark.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    crawler = GoogleImageCrawler(storage={'root_dir': folder})
    crawler.crawl(keyword=landmark, max_num=images_per_landmark)

print("\n✅ Done! All images are saved inside the 'landmarks/' folder.")
