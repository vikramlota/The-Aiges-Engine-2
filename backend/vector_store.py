import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sklearn.feature_extraction.text import HashingVectorizer
from backend.config import CHROMA_PERSIST_DIR

# Persistent ChromaDB client
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
_chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Deterministic HashingVectorizer with L2 normalization (cosine distance compatible)
_vectorizer = HashingVectorizer(n_features=256, norm="l2", alternate_sign=False)

# Get or create collection using cosine distance space
_collection = _chroma_client.get_or_create_collection(
    name="audit_captions",
    metadata={"hnsw:space": "cosine"}
)


def extract_features(text: str) -> List[float]:
    """Extract deterministic normalized vector features from caption text."""
    if not text or not text.strip():
        text = "empty"
    vector = _vectorizer.transform([text]).toarray()[0].tolist()
    return vector


def index_audit(
    audit_id: int,
    owner_id: int,
    caption: str,
    status: str,
    risk_level: Optional[str] = None
) -> None:
    """Index an audit's caption and metadata in ChromaDB."""
    if not caption or not caption.strip():
        return

    vector = extract_features(caption)
    _collection.upsert(
        ids=[str(audit_id)],
        embeddings=[vector],
        documents=[caption],
        metadatas=[{
            "audit_id": audit_id,
            "owner_id": owner_id,
            "status": status,
            "risk_level": risk_level or "NONE"
        }]
    )


def find_similar_audits(
    caption: str,
    owner_id: int,
    exclude_id: Optional[int] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Find similar past audits for the same user based on caption vector similarity."""
    if not caption or not caption.strip():
        return []

    # Count total documents in collection
    count = _collection.count()
    if count == 0:
        return []

    vector = extract_features(caption)
    # Fetch a few extra candidates so we can exclude the current audit_id if needed
    query_k = min(count, top_k + 2)

    try:
        results = _collection.query(
            query_embeddings=[vector],
            n_results=query_k,
            where={"owner_id": owner_id}
        )
    except Exception:
        return []

    similar = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for item_id, distance, doc, meta in zip(ids, distances, documents, metadatas):
        parsed_id = int(item_id)
        if exclude_id is not None and parsed_id == exclude_id:
            continue

        # Cosine distance to similarity: similarity = 1 - distance
        similarity = round(max(0.0, min(1.0, 1.0 - float(distance))), 2)

        risk = meta.get("risk_level")
        similar.append({
            "id": parsed_id,
            "caption": doc,
            "status": meta.get("status", "UNKNOWN"),
            "risk_level": None if risk == "NONE" else risk,
            "similarity": similarity
        })

        if len(similar) >= top_k:
            break

    return similar
