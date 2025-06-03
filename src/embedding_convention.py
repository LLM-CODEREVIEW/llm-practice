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
logger = logging.getLogger(__name__)
logger.info("=== ChromaDB 초기화 시작 ===")
try:
    # 기존 DB 사용
    client = PersistentClient(path="./chroma_db", settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    ))
    logger.info(f"ChromaDB 클라이언트 초기화 성공: ./chroma_db")
    
    # 컬렉션 직접 생성
    java_collection = client.get_or_create_collection(
        name="java_style_rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None
    )
    swift_collection = client.get_or_create_collection(
        name="swift_style_rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None
    )
    logger.info("컬렉션 초기화 완료")
    
except Exception as e:
    logger.error(f"ChromaDB 초기화 실패: {str(e)}")
    raise

# 컬렉션 목록 확인
collections = client.list_collections()
print(f"생성된 컬렉션 목록: {collections}")

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
