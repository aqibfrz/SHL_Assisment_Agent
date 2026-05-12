import json
from src.rag.embeddings import get_embedding
from src.rag.vector_store import add_embeddings, reset_index, save_index


def extract_products(raw_data):
    """
    SHL JSON is nested. This safely extracts the product list.
    """
    if isinstance(raw_data, list):
        return raw_data

    # Try common keys
    for key in ["products", "data", "catalog", "assessments"]:
        if key in raw_data:
            return raw_data[key]

    raise ValueError("❌ Could not find product list in JSON")

def extract_test_type(item):
    # Try common keys
    if item.get("testType"):
        return item["testType"]

    if item.get("test_type"):
        return item["test_type"]

    if item.get("type"):
        return item["type"]

    # Try nested structure
    if "categories" in item:
        for cat in item["categories"]:
            name = cat.get("name", "").lower()

            if "knowledge" in name:
                return "K"
            elif "personality" in name:
                return "P"
            elif "ability" in name:
                return "A"
            elif "simulation" in name:
                return "S"

    # fallback
    return "Unknown"

def normalize_catalog(data):
    normalized = []

    for item in data:
        name = item.get("name") or item.get("title") or ""

        url = (
            item.get("url")
            or item.get("productUrl")
            or item.get("link")
        )

        description = item.get("description") or ""

        test_type = extract_test_type(item)

        if not name or not url:
            continue

        normalized.append({
            "name": name,
            "url": url,
            "test_type": test_type,
            "description": description,
            "text": f"{name} {description}"
        })

    return normalized

def build_index():
    reset_index()
    print("🔄 Loading dataset...")

    with open("data/SHL_catalogue.json", encoding="utf-8") as f:
        raw_data = json.load(f)

    # IMPORTANT: extract correct level
    products = extract_products(raw_data)

    print(f"📦 Found {len(products)} raw items")

    data = normalize_catalog(products)

    texts = [d["text"] for d in data]
    vectors = [get_embedding(t)[0] for t in texts]

    add_embeddings(vectors, data)
    save_index()

    print("✅ FAISS index built successfully")