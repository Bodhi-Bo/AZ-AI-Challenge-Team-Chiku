"""
Utility for generating and comparing text embeddings using sentence-transformers.
Uses all-MiniLM-L6-v2 model for efficient semantic search.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)

# Load model once at module level (singleton pattern)
# all-MiniLM-L6-v2: 384 dimensions, fast, good for short texts
_model = None


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully")
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a given text.

    Args:
        text: Text to embed (e.g., event title)

    Returns:
        List of floats representing the embedding vector (384 dimensions)
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Similarity score between 0 and 1 (1 = identical, 0 = completely different)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    # Cosine similarity = dot product / (norm1 * norm2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return float(similarity)


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    threshold: float = 0.7,
) -> List[tuple[int, float]]:
    """
    Find the most similar embeddings to a query embedding.

    Args:
        query_embedding: The query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        threshold: Minimum similarity score to include (0-1)

    Returns:
        List of (index, similarity_score) tuples sorted by score (highest first)
        Only includes results above the threshold
    """
    results = []

    for idx, candidate in enumerate(candidate_embeddings):
        similarity = cosine_similarity(query_embedding, candidate)
        if similarity >= threshold:
            results.append((idx, similarity))

    # Sort by similarity score (descending)
    results.sort(key=lambda x: x[1], reverse=True)

    return results
