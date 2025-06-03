from worker import *
from sentence_transformers import SentenceTransformer
from prompt.xmlStyle import template
import chromadb

# Step 1: PR Diff 입력
diff_input = """ """

# Step 2: 코딩컨벤션 키워드를 도출하는 LLM 프롬프트 구성
prompt = get_convention_keyword_prompt(diff_input)

# Step 3: Ollama 실행 및 vectorDB 가져오기
process = run_ollama(prompt)
output_text = process.stdout.decode("utf-8")
violation_sentences = export_json_array(output_text)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")

# 사용되는 언어에 따라 vectorDB 다르게 조회
detected_language = detect_language(diff_input)
collection_name = f"{detected_language}_style_rules"
collection = client.get_collection(collection_name)

# STEP 4: vectorDB에서 코딩컨벤션 키워드와 매칭되는 부분 찾기
convention_guide = ""
for sentence in violation_sentences:
    vec = model.encode(sentence).tolist()
    results = collection.query(query_embeddings=[vec], n_results=1)
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        convention_guide += f"- [{meta['category']}] {doc.strip()}\n"
# 도출된 코딩컨벤션 키워드가 없는 경우 PASS
if convention_guide == "":
    convention_guide = "not applicable"

# STEP 5: 코딩 컨벤션 검증까지 완료한 프롬포트 생성완료
final_prompt = (
    template
    .replace("{{CONVENTION_GUIDE_PLACEHOLDER}}", convention_guide.strip())
    .replace("{{PR_DIFF_PLACEHOLDER}}", diff_input.strip())
)
print(final_prompt)

# STEP 6: 최종 프롬프트로 Ollama 실행
response = run_ollama(final_prompt)

# RESULT!!!!
print(response.stdout.decode("utf-8"))