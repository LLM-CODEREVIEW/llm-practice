import requests
import json
from loguru import logger
from typing import Dict, List, Any
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

class CodeLlamaReviewer:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self._check_ollama()
        self.max_workers = 3  # 동시에 처리할 파일 수

    def _check_ollama(self):
        """Ollama API 서버 연결 확인"""
        try:
            response = requests.get(f"{self.api_url}/api/tags")
            response.raise_for_status()
            logger.info("Ollama API 서버 연결 성공")
        except Exception as e:
            logger.error(f"Ollama API 서버 연결 실패: {str(e)}")
            raise

    def _create_prompt(self, code: str) -> str:
        """코드 리뷰를 위한 프롬프트를 생성합니다."""
        return f"""아래는 GitHub Pull Request의 diff patch입니다.

- patch의 각 줄에서 +로 시작하는 줄(즉, 실제로 변경/추가된 코드)에만 코멘트를 달아주세요.
- 전체 코드를 이해하고, 변경된 줄(+)에만 코멘트가 필요하다고 판단되는 경우에만 코멘트를 작성하세요.
- 반드시 아래 형식을 정확히 지켜서 작성하세요:

Line: [patch에서 +로 시작하는 줄의 실제 라인 번호]
Severity: [HIGH|MEDIUM|LOW]
Category: [BUG|PERFORMANCE|READABILITY|SECURITY|OTHER]
Description: [문제 설명]
Proposed Solution: [개선 방안]

예시:
Line: 5
Severity: HIGH
Category: BUG
Description: This line has a potential bug
Proposed Solution: Fix the bug by doing X

주의사항:
1. Line 필드는 반드시 포함되어야 합니다
2. Severity는 HIGH, MEDIUM, LOW 중 하나만 사용하세요
3. Category는 BUG, PERFORMANCE, READABILITY, SECURITY, OTHER 중 하나만 사용하세요
4. 각 필드는 정확히 위 형식대로 작성하세요

아래는 diff patch입니다:
{code}

리뷰 결과:"""

    def _parse_review_result(self, review_text: str) -> List[Dict[str, Any]]:
        """LLM 리뷰 결과를 파싱하여 구조화된 형태로 변환합니다."""
        comments = []
        current_comment = {}
        
        # 각 이슈 블록을 분리
        blocks = re.split(r'\n(?=Line:|라인:)', review_text)
        
        for block in blocks:
            if not block.strip():
                continue
                
            # 필수 필드 확인
            line_match = re.search(r'(?:Line|라인):\s*(\d+)', block)
            severity_match = re.search(r'(?:Severity|심각도):\s*(HIGH|MEDIUM|LOW)', block)
            category_match = re.search(r'(?:Category|카테고리):\s*(BUG|PERFORMANCE|READABILITY|SECURITY|OTHER)', block)
            description_match = re.search(r'(?:Description|설명):\s*(.*?)(?=\n(?:Proposed Solution|제안):|\Z)', block, re.DOTALL)
            solution_match = re.search(r'(?:Proposed Solution|제안):\s*(.*?)(?=\n(?:Line|라인):|\Z)', block, re.DOTALL)
            
            if not all([line_match, severity_match, category_match, description_match]):
                logger.warning(f"[DEBUG] 필수 필드 누락된 블록: {block}")
                continue
                
            comment = {
                'line': int(line_match.group(1)),
                'severity': severity_match.group(1),
                'category': category_match.group(1),
                'description': description_match.group(1).strip(),
                'proposal': solution_match.group(1).strip() if solution_match else ""
            }
            comments.append(comment)
        
        return comments

    def _review_single_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """단일 파일 리뷰 수행"""
        filename = file_data.get('filename', '')
        content = file_data.get('patch', '')
        
        if not content:
            logger.warning(f"파일 내용이 비어있습니다: {filename}")
            return None

        logger.info(f"리뷰 중: {filename}")
        start_time = time.time()
        
        try:
            # Ollama API 호출
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": "codellama:13b",
                    "prompt": self._create_prompt(content),
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                logger.error(f"API 호출 실패: {response.status_code}")
                return None

            result = response.json()
            review_text = result['response']
            
            logger.info(f"[DEBUG] LLM 응답 원본:\n{review_text}")
            try:
                parsed_comments = self._parse_review_result(review_text)
                logger.info(f"[DEBUG] 파싱된 리뷰 코멘트: {parsed_comments}")
            except Exception as e:
                logger.error(f"[DEBUG] 리뷰 파싱 중 예외 발생: {str(e)}")
                parsed_comments = []
            
            # 리뷰 결과 로깅
            logger.info(f"파일 {filename} 리뷰 결과:\n{review_text}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"파일 {filename} 리뷰 완료 (소요시간: {elapsed_time:.2f}초)")
            
            return {
                'file': filename,
                'review': review_text,
                'comments': parsed_comments
            }
            
        except Exception as e:
            logger.error(f"파일 {filename} 리뷰 중 오류 발생: {str(e)}")
            return None

    def review_code(self, pr_data: dict) -> dict:
        """PR의 코드를 리뷰"""
        try:
            review_results = []
            changed_files = pr_data.get('changed_files', [])
            
            # 병렬 처리로 파일 리뷰 수행
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._review_single_file, file_data): file_data
                    for file_data in changed_files
                }
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    if result:
                        review_results.append(result)

            return {
                'pr_number': pr_data.get('number', ''),
                'title': pr_data.get('title', ''),
                'reviews': review_results
            }

        except Exception as e:
            logger.error(f"코드 리뷰 중 오류 발생: {str(e)}")
            raise 