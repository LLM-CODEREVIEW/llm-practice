import requests
import json
from loguru import logger
from typing import Dict, List, Any
import os

class CodeLlamaReviewer:
    def __init__(self, model_name: str = "codellama"):
        self.model_name = model_name
        self.api_base = "http://localhost:11434/api"
        self._check_ollama()

    def _check_ollama(self):
        """Ollama 서버가 실행 중인지 확인합니다."""
        try:
            response = requests.get(f"{self.api_base}/tags")
            if response.status_code != 200:
                raise Exception("Ollama 서버에 연결할 수 없습니다.")
            logger.info("Ollama 서버 연결 성공")
        except Exception as e:
            logger.error(f"Ollama 서버 연결 실패: {str(e)}")
            raise

    def _create_prompt(self, file_data: Dict[str, Any]) -> str:
        """코드 리뷰를 위한 프롬프트를 생성합니다."""
        prompt = f"""다음 코드를 리뷰해주세요. 각 문제점에 대해 다음 형식으로 응답해주세요:

파일: {file_data['filename']}
라인 번호: [문제가 있는 라인 번호]
심각도: [HIGH/MEDIUM/LOW]
카테고리: [BUG/PERFORMANCE/READABILITY/SECURITY/OTHER]
설명: [문제점 설명]
제안: [개선 제안]

코드:
{file_data['patch']}

리뷰:"""
        return prompt

    def _process_model_response(self, response: str, file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """모델의 응답을 구조화된 형식으로 변환합니다."""
        issues = []
        current_issue = {}
        
        for line in response.split('\n'):
            if line.startswith('라인 번호:'):
                if current_issue:
                    issues.append(current_issue)
                current_issue = {
                    'file': file_data['filename'],
                    'line_number': int(line.split(':')[1].strip()),
                    'severity': '',
                    'category': '',
                    'description': '',
                    'suggestion': ''
                }
            elif line.startswith('심각도:'):
                current_issue['severity'] = line.split(':')[1].strip()
            elif line.startswith('카테고리:'):
                current_issue['category'] = line.split(':')[1].strip()
            elif line.startswith('설명:'):
                current_issue['description'] = line.split(':')[1].strip()
            elif line.startswith('제안:'):
                current_issue['suggestion'] = line.split(':')[1].strip()

        if current_issue:
            issues.append(current_issue)

        return issues

    def review_code(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """PR의 코드를 리뷰합니다."""
        all_issues = []
        
        try:
            for file_data in pr_data['changed_files']:
                prompt = self._create_prompt(file_data)
                
                # Ollama API 호출
                response = requests.post(
                    f"{self.api_base}/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API 호출 실패: {response.text}")
                
                response_data = response.json()
                issues = self._process_model_response(response_data['response'], file_data)
                all_issues.extend(issues)

            return all_issues

        except Exception as e:
            logger.error(f"Error reviewing code: {str(e)}")
            raise 