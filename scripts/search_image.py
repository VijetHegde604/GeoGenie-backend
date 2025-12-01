"""
Image search using FAISS for similarity matching.
Compares query image embeddings against reference database.
"""

import faiss
import numpy as np
from typing import Tuple, List, Dict
import os
import pickle


class ImageSearch:
    """FAISS-based image similarity search."""
    
    def __init__(self, db_path: str = "data/landmarks_db.faiss", metadata_path: str = "data/landmarks_metadata.pkl"):
        """
        Initialize image search with FAISS index.
        
        Args:
            db_path: Path to FAISS index file
            metadata_path: Path to metadata pickle file
        """
        self.db_path = db_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = []
        self.dimension = 512  # CLIP ViT-B/32 embedding dimension
        
        self._load_database()
    
    def _load_database(self):
        """Load FAISS index and metadata from disk."""
        try:
            if os.path.exists(self.db_path) and os.path.exists(self.metadata_path):
                self.index = faiss.read_index(self.db_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"Loaded database with {self.index.ntotal} landmarks.")
            else:
                # Create empty index
                self.index = faiss.IndexFlatL2(self.dimension)
                print("Created new empty database.")
        except Exception as e:
            print(f"Error loading database: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def _save_database(self):
        """Save FAISS index and metadata to disk."""
        try:
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
            faiss.write_index(self.index, self.db_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            print(f"Saved database with {self.index.ntotal} landmarks.")
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def add_landmark(self, embedding: np.ndarray, place_name: str, image_path: str = None):
        """
        Add a landmark to the database.
        
        Args:
            embedding: Normalized embedding vector
            place_name: Name of the place
            image_path: Optional path to reference image
        """
        if embedding.shape[0] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {embedding.shape[0]}")
        
        # Ensure embedding is float32 and normalized
        embedding = embedding.astype('float32').reshape(1, -1)
        
        # Prevent adding duplicates for the same place_name
        for md in self.metadata:
            if md.get("place_name") == place_name:
                print(f"Skipping add: {place_name} already exists in FAISS metadata")
                return

        # Add to index
        self.index.add(embedding)
        
        # Add metadata
        self.metadata.append({
            "place_name": place_name,
            "image_path": image_path,
            "index": self.index.ntotal - 1
        })
        
        self._save_database()
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search for similar landmarks.
        
        Args:
            query_embedding: Normalized embedding vector of query image
            k: Number of results to return
            
        Returns:
            List of dictionaries with place_name, confidence, and metadata
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure embedding is float32 and normalized
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                # Convert L2 distance to similarity (cosine similarity for normalized vectors)
                # For normalized vectors, L2 distance relates to cosine similarity:
                # cosine_sim = 1 - (L2_distance^2 / 2)
                similarity = max(0.0, 1.0 - (distance / 2.0))
                
                result = {
                    "place_name": self.metadata[idx]["place_name"],
                    "confidence": float(similarity),
                    "distance": float(distance),
                    "metadata": self.metadata[idx]
                }
                results.append(result)
        
        return results
    
    def get_best_match(self, query_embedding: np.ndarray, threshold: float = 0.7) -> Dict:
        """
        Get best matching landmark if confidence exceeds threshold.
        
        Args:
            query_embedding: Normalized embedding vector
            threshold: Minimum confidence threshold
            
        Returns:
            Best match dictionary or None
        """
        results = self.search(query_embedding, k=1)
        if results and results[0]["confidence"] >= threshold:
            return results[0]
        return None


# Global instance
_search_engine = None


def get_search_engine() -> ImageSearch:
    """Get or create global search engine instance."""
    global _search_engine
    if _search_engine is None:
        _search_engine = ImageSearch()
    return _search_engine

