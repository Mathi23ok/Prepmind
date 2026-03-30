from config import get_settings
from models.faiss_store import get_chunks_with_docs, search, user_chunks
from services.embedding_service import get_embedding


def retrieve_chunks(user_id, query, document_name=None):
    settings = get_settings()

    if user_id not in user_chunks or len(user_chunks[user_id]) == 0:
        return None, None

    query_vector = get_embedding(query).reshape(1, -1)
    k = len(user_chunks[user_id]) if document_name else min(settings.top_k_chunks, len(user_chunks[user_id]))

    distances, indices = search(user_id, query_vector, k)
    indexed_chunks = get_chunks_with_docs(user_id, indices[0])

    filtered_results = []
    filtered_distances = []

    for position, item in enumerate(indexed_chunks):
        if document_name and item["document_name"] != document_name:
            continue

        filtered_results.append(item)
        filtered_distances.append(distances[0][position])

        if len(filtered_results) == 5:
            break

    if not filtered_results or filtered_distances[0] > settings.similarity_threshold:
        return None, None

    return filtered_results, filtered_distances
