"""
CLIP embedding generator for image feature extraction.
Uses OpenAI's CLIP model to generate embeddings for landmark recognition.
"""

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from typing import Union
import io


class EmbeddingGenerator:
    """Generates CLIP embeddings for images."""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize CLIP model and processor.
        
        Args:
            model_name: HuggingFace model identifier for CLIP
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading CLIP model on {self.device}...")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()
        print("CLIP model loaded successfully.")
    
    def generate_embedding(self, image: Union[Image.Image, bytes, str]) -> np.ndarray:
        """
        Generate embedding vector for an image.
        
        Args:
            image: PIL Image, bytes, or file path
            
        Returns:
            Normalized embedding vector as numpy array
        """
        # Convert input to PIL Image if needed
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        elif isinstance(image, str):
            image = Image.open(image)
        
        # Process image and generate embedding
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            image_features = self.model.get_image_features(**inputs)
            # Normalize the embedding
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embedding = image_features.cpu().numpy().flatten()
        
        return embedding
    
    def generate_embeddings_batch(self, images: list) -> np.ndarray:
        """
        Generate embeddings for multiple images (batch processing).
        
        Args:
            images: List of PIL Images, bytes, or file paths
            
        Returns:
            Array of normalized embedding vectors
        """
        # Convert all inputs to PIL Images
        pil_images = []
        for img in images:
            if isinstance(img, bytes):
                pil_images.append(Image.open(io.BytesIO(img)))
            elif isinstance(img, str):
                pil_images.append(Image.open(img))
            else:
                pil_images.append(img)
        
        # Process batch
        with torch.no_grad():
            inputs = self.processor(images=pil_images, return_tensors="pt").to(self.device)
            image_features = self.model.get_image_features(**inputs)
            # Normalize embeddings
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embeddings = image_features.cpu().numpy()
        
        return embeddings


# Global instance (lazy-loaded)
_embedder = None


def get_embedder() -> EmbeddingGenerator:
    """Get or create global embedding generator instance."""
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingGenerator()
    return _embedder

