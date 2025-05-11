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
- 각 코멘트는 아래 형식으로 작성하세요:

Line: [patch에서 +로 시작하는 줄의 실제 라인 번호]
Severity: [HIGH|MEDIUM|LOW]
Category: [BUG|PERFORMANCE|READABILITY|SECURITY|OTHER]
Description: [문제 설명]
Proposed Solution: [개선 방안]

아래는 diff patch입니다:
{code}

리뷰 결과:"""

    def _parse_review_result(self, review_text: str) -> List[Dict[str, Any]]:
        """LLM 리뷰 결과를 파싱하여 구조화된 형태로 변환합니다. 구간이 오면 첫 번째 숫자만 사용합니다."""
        comments = []
        current_comment = {}
        
        for line in review_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('라인:') or line.startswith('Line:'):
                if current_comment:
                    comments.append(current_comment)
                # 구간/복수 라인에서 첫 번째 숫자만 추출
                line_field = line.split(':', 1)[1].strip()
                m = re.match(r'^(\d+)', line_field)
                if m:
                    first_line = int(m.group(1))
                    current_comment = {'line': first_line}
                else:
                    current_comment = {}
            elif line.startswith('심각도:') or line.startswith('Severity:'):
                current_comment['severity'] = line.split(':', 1)[1].strip()
            elif line.startswith('카테고리:') or line.startswith('Category:'):
                current_comment['category'] = line.split(':', 1)[1].strip()
            elif line.startswith('설명:') or line.startswith('Description:'):
                current_comment['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('제안:') or line.startswith('Proposal:') or line.startswith('Proposed solution:'):
                current_comment['proposal'] = line.split(':', 1)[1].strip()
                
        if current_comment:
            comments.append(current_comment)
            
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