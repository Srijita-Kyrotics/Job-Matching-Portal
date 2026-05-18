import logging
from sentence_transformers import SentenceTransformer
from typing import List

logger = logging.getLogger("embeddings")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# Cache model instance in memory for high-performance lazy loading
_model_instance = None

def get_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        try:
            logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2' (384 dimensions)...")
            _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer: {e}", exc_info=True)
            _model_instance = None
    return _model_instance

def generate_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding generation. Returning zero vector.")
        return [0.0] * 384
        
    model = get_model()
    if model is None:
        logger.error("SentenceTransformer model is unavailable. Falling back to zero-vector embedding.")
        return [0.0] * 384
        
    try:
        logger.info(f"Generating embedding for text block of length {len(text)}...")
        # Encode text into 384-dimensional dense semantic vector
        vector = model.encode(text, convert_to_numpy=True)
        logger.info("Dense vector embedding generated successfully.")
        return vector.tolist()
    except Exception as e:
        logger.error(f"Error generating semantic embedding: {e}", exc_info=True)
        return [0.0] * 384

