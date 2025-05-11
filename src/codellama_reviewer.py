import requests
import json
from loguru import logger
from typing import Dict, List, Any
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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
        return f"""다음 코드를 리뷰해주세요. 각 이슈에 대해 다음 형식으로 응답해주세요:

라인: [문제가 있는 라인 번호]
심각도: [HIGH/MEDIUM/LOW]
카테고리: [BUG/PERFORMANCE/READABILITY/SECURITY/OTHER]
설명: [구체적인 문제 설명]
제안: [개선 방안]

코드:
{code}

리뷰 결과:"""

    def _parse_review_result(self, review_text: str) -> List[Dict[str, Any]]:
        """LLM 리뷰 결과를 파싱하여 구조화된 형태로 변환합니다."""
        comments = []
        current_comment = {}
        
        for line in review_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('라인:'):
                if current_comment:
                    comments.append(current_comment)
                current_comment = {'line': int(line.split(':')[1].strip())}
            elif line.startswith('심각도:'):
                current_comment['severity'] = line.split(':')[1].strip()
            elif line.startswith('카테고리:'):
                current_comment['category'] = line.split(':')[1].strip()
            elif line.startswith('설명:'):
                current_comment['description'] = line.split(':')[1].strip()
            elif line.startswith('제안:'):
                current_comment['proposal'] = line.split(':')[1].strip()
                
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
            
            # 리뷰 결과 파싱
            parsed_comments = self._parse_review_result(review_text)
            
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