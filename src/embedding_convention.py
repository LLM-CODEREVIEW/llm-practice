from sentence_transformers import SentenceTransformer
import chromadb
import json
from chromadb import PersistentClient
import logging

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
try:
    # 클라이언트 생성
    client = PersistentClient(path="./chroma_db", settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True
    ))
    
    # 연결 테스트
    try:
        collections = client.list_collections()
        print(f"ChromaDB 연결 성공: {len(collections)} 개의 컬렉션 발견")
    except Exception as e:
        print(f"ChromaDB 연결 테스트 실패: {str(e)}")
        raise

    # Create separate collections for Java and Swift rules
    java_collection = client.create_collection(
        name="java_style_rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None  # sentence-transformers를 직접 사용하므로 None
    )
    print("=== Java 컬렉션 생성 완료 ===")

    swift_collection = client.create_collection(
        name="swift_style_rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None  # sentence-transformers를 직접 사용하므로 None
    )
    print("=== Swift 컬렉션 생성 완료 ===")

    # 컬렉션 목록 확인
    collections = client.list_collections()
    print(f"생성된 컬렉션 목록: {collections}")

except Exception as e:
    print(f"ChromaDB 초기화 실패: {str(e)}")
    raise

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
