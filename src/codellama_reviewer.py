import requests
import json
from loguru import logger
from typing import Dict, List, Any
import os

class CodeLlamaReviewer:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self._check_ollama()

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
        """코드 리뷰를 위한 프롬프트 생성"""
        return f"""다음 코드를 리뷰해주세요. 코드의 품질, 보안, 성능, 가독성 등을 검토하고 개선점을 제안해주세요.

코드:
{code}

리뷰 형식:
1. 전체적인 평가
2. 주요 문제점
3. 개선 제안
4. 보안 관련 이슈
5. 성능 관련 이슈
6. 가독성 관련 이슈

각 이슈는 다음 형식으로 작성해주세요:
- 심각도: [HIGH/MEDIUM/LOW]
- 설명: [이슈 설명]
- 제안: [개선 방안]
"""

    def review_code(self, pr_data: dict) -> dict:
        """PR의 코드를 리뷰"""
        try:
            review_results = []
            
            # PR 데이터에서 변경된 파일 목록 가져오기
            changed_files = pr_data.get('changed_files', [])
            
            for file_data in changed_files:
                filename = file_data.get('filename', '')
                if not filename.endswith(('.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp')):
                    continue

                logger.info(f"리뷰 중: {filename}")
                
                # 파일 내용 가져오기
                content = file_data.get('patch', '')
                if not content:
                    logger.warning(f"파일 내용이 비어있습니다: {filename}")
                    continue
                
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
                    continue

                result = response.json()
                review_results.append({
                    'file': filename,
                    'review': result['response']
                })

            return {
                'pr_number': pr_data.get('number', ''),
                'title': pr_data.get('title', ''),
                'reviews': review_results
            }

        except Exception as e:
            logger.error(f"코드 리뷰 중 오류 발생: {str(e)}")
            raise 