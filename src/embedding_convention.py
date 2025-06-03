from sentence_transformers import SentenceTransformer
import chromadb
import json
from chromadb import PersistentClient

# Load style rules JSON
with open("src/style_guide/java_style_rules.json", encoding="utf-8") as f:
    java_data = json.load(f)
java_rules = java_data["java_style_guide_rules"]

with open("src/style_guide/swift_style_rules.json", encoding="utf-8") as f:
    swift_data = json.load(f)
swift_rules = swift_data["swift_style_guide_rules"]

# Load model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Setup ChromaDB
client = PersistentClient(path="chroma_db")

# Create separate collections for Java and Swift rules
java_collection = client.get_or_create_collection("java_style_rules")
swift_collection = client.get_or_create_collection("swift_style_rules")

# Embed and store Java rules
for rule in java_rules:
    doc = f"{rule['title']}\n{rule['rule']}"
    emb = model.encode(doc).tolist()
    java_collection.add(
        documents=[doc],
        embeddings=[emb],
        ids=[rule["id"]],
        metadatas=[{
            "category": rule["category"],
            "subcategory": rule["subcategory"],
            "title": rule["title"]
        }]
    )

# Embed and store Swift rules
for rule in swift_rules:
    doc = f"{rule['title']}\n{rule['rule']}"
    emb = model.encode(doc).tolist()
    swift_collection.add(
        documents=[doc],
        embeddings=[emb],
        ids=[rule["id"]],
        metadatas=[{
            "category": rule["category"],
            "subcategory": rule["subcategory"],
            "title": rule["title"]
        }]
    )
print("✅ Embedding complete and saved.")
