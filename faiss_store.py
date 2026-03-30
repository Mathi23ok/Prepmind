import faiss
import numpy as np

dimension = 384

user_indices = {}
user_chunks = {}
user_chunk_docs = {}
user_documents = {}


def get_or_create_index(user_id):
    if user_id not in user_indices:
        user_indices[user_id] = faiss.IndexFlatL2(dimension)
        user_chunks[user_id] = []
        user_chunk_docs[user_id] = []
        user_documents[user_id] = []
    return user_indices[user_id]


def add_embeddings(user_id, document_name, chunks, embeddings):
    index = get_or_create_index(user_id)
    user_chunks[user_id].extend(chunks)
    user_chunk_docs[user_id].extend([document_name] * len(chunks))

    if document_name not in user_documents[user_id]:
        user_documents[user_id].append(document_name)

    index.add(np.array(embeddings))


def search(user_id, query_vector, k):
    index = get_or_create_index(user_id)
    return index.search(query_vector, k)


def get_chunks(user_id, indices):
    return [user_chunks[user_id][i] for i in indices]


def get_chunks_with_docs(user_id, indices):
    return [
        {
            "chunk": user_chunks[user_id][i],
            "document_name": user_chunk_docs[user_id][i],
        }
        for i in indices
    ]


def list_documents(user_id):
    get_or_create_index(user_id)
    return user_documents[user_id]
