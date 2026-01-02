"""
Build reference database of landmark embeddings.
Creates FAISS index from sample landmarks for demonstration.
"""

import os
from embed_generator import EmbeddingGenerator
from search_image import ImageSearch
from PIL import Image
import numpy as np


def build_database_from_images(image_dir: str):
    """
    Build database from directory of landmark images.
    
    Args:
        image_dir: Directory containing landmark images
                   Expected structure: image_dir/landmark_name/*.jpg
    """
    print(f"Building database from images in {image_dir}...")
    
    embedder = EmbeddingGenerator()
    search_engine = ImageSearch()
    
    if not os.path.exists(image_dir):
        print(f"Directory {image_dir} does not exist.")
        return
    
    # Walk through directory structure
    for root, dirs, files in os.walk(image_dir):
        landmark_name = os.path.basename(root)
        if landmark_name == os.path.basename(image_dir):
            continue  # Skip root directory
        
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not image_files:
            continue
        
        # Use first image as reference
        image_path = os.path.join(root, image_files[0])
        try:
            image = Image.open(image_path)
            embedding = embedder.generate_embedding(image)
            
            search_engine.add_landmark(
                embedding=embedding,
                place_name=landmark_name,
                image_path=image_path
            )
            print(f"Added: {landmark_name} from {image_path}")
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    
    print(f"Database built with {search_engine.index.ntotal} landmarks.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python build_db.py <image_directory>")
        sys.exit(1)

    image_dir = sys.argv[1]
    build_database_from_images(image_dir)

