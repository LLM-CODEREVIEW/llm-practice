from worker import get_convention_keyword_prompt, run_ollama, export_json_array
from sentence_transformers import SentenceTransformer
import chromadb
from prompt.xmlStyle import template
from typing import Optional

class CodingConventionVerifier:
    def __init__(self, chroma_db_path: str = "./chroma_db"):
        """코딩 컨벤션 검증기를 초기화합니다."""
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=chroma_db_path)

    def _detect_language(self, code: str) -> str:
        """코드에서 언어를 감지합니다."""
        if ".java" in code:
            return "java"
        elif ".swift" in code:
            return "swift"
        return "java"  # 기본값

    def _get_convention_guide(self, code: str) -> str:
        """코드에 대한 코딩 컨벤션 가이드를 검색합니다."""
        # 코딩컨벤션 키워드 도출
        convention_prompt = get_convention_keyword_prompt(code)
        process = run_ollama(convention_prompt)
        output_text = process.stdout.decode("utf-8")
        violation_sentences = export_json_array(output_text)

        # VectorDB에서 관련 컨벤션 가이드 찾기
        detected_language = self._detect_language(code)
        collection_name = f"{detected_language}_style_rules"
        collection = self.client.get_collection(collection_name)

        # 관련 컨벤션 가이드 수집
        convention_guide = ""
        for sentence in violation_sentences:
            vec = self.model.encode(sentence).tolist()
            results = collection.query(query_embeddings=[vec], n_results=1)
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                convention_guide += f"- [{meta['category']}] {doc.strip()}\n"

        return convention_guide.strip() if convention_guide else "not applicable"

    def create_review_prompt(self, code: str) -> str:
        """코드 리뷰를 위한 프롬프트를 생성합니다."""
        convention_guide = self._get_convention_guide(code)
        
        # xmlStyle.py의 템플릿 사용
        final_prompt = (
            template
            .replace("{{CONVENTION_GUIDE_PLACEHOLDER}}", convention_guide)
            .replace("{{PR_DIFF_PLACEHOLDER}}", code.strip())
        )

        return final_prompt 