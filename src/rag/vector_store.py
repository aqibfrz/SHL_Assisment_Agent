import faiss
import numpy as np
import pickle
import os

index = faiss.IndexFlatL2(384)
documents = []


def reset_index():
    global index, documents
    index = faiss.IndexFlatL2(384)
    documents = []


def add_embeddings(vectors, docs):
    global documents
    index.add(np.array(vectors))
    documents.extend(docs)

def save_index():
    os.makedirs("artifacts/faiss_index", exist_ok=True)
    faiss.write_index(index, "artifacts/faiss_index/index.faiss")
    
    with open("artifacts/faiss_index/docs.pkl", "wb") as f:
        pickle.dump(documents, f)

def load_index():
    global index, documents
    index = faiss.read_index("artifacts/faiss_index/index.faiss")
    
    with open("artifacts/faiss_index/docs.pkl", "rb") as f:
        documents = pickle.load(f)

def search_index(query_vector, k=5):
    distances, indices = index.search(query_vector, k)
    n = len(documents)
    result = []
    for i in indices[0]:
        if 0 <= int(i) < n:
            result.append(documents[i])
    return result