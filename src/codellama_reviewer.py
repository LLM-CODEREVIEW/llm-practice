import requests
import json
from loguru import logger
from typing import Dict, List, Any
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
import subprocess
import atexit
import signal

class CodeLlamaReviewer:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.ssh_process = None
        self._setup_ssh_tunnel()
        self._check_ollama()
        self.max_workers = 3  # 동시에 처리할 파일 수

    def _setup_ssh_tunnel(self):
        """SSH 터널을 설정합니다."""
        try:
            host = os.getenv('LLM_SERVER_HOST')
            user = os.getenv('LLM_SERVER_USER')
            port = os.getenv('LLM_SERVER_PORT', '22')
            
            if not all([host, user]):
                logger.error("SSH 연결에 필요한 환경 변수가 설정되지 않았습니다.")
                raise ValueError("Missing required environment variables for SSH connection")

            # StrictHostKeyChecking=no 옵션 추가
            ssh_cmd = f'ssh -o StrictHostKeyChecking=no -N -L 8080:localhost:11434 {user}@{host} -p {port}'
            self.ssh_process = pexpect.spawn(ssh_cmd)
            
            i = self.ssh_process.expect([
                'Are you sure you want to continue connecting (yes/no/[fingerprint])?',
                'password:',
                pexpect.EOF,
                pexpect.TIMEOUT
            ], timeout=30)

            if i == 0:
                self.ssh_process.sendline('yes')
                self.ssh_process.expect('password:')
                self.ssh_process.sendline(password)
            elif i == 1:
                self.ssh_process.sendline(password)
            else:
                raise Exception('SSH 연결 실패')

            # 프로세스 종료 시 SSH 터널도 종료되도록 설정
            atexit.register(self._cleanup_ssh_tunnel)
            signal.signal(signal.SIGTERM, self._cleanup_ssh_tunnel)
            
            # 터널이 설정될 때까지 잠시 대기
            time.sleep(2)
            
            # API URL을 로컬 터널 포인트로 변경
            self.api_url = "http://localhost:8080"
            logger.info("SSH 터널이 성공적으로 설정되었습니다.")
            
        except Exception as e:
            logger.error(f"SSH 터널 설정 중 오류 발생: {str(e)}")
            raise

    def _cleanup_ssh_tunnel(self, *args):
        """SSH 터널을 정리합니다."""
        if self.ssh_process:
            self.ssh_process.terminate()
            self.ssh_process.wait()
            logger.info("SSH 터널이 종료되었습니다.")

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
        # patch에서 +로 시작하는 줄의 라인 번호 추출
        patch_lines = []
        for i, line in enumerate(code.split('\n'), 1):
            if line.startswith('+') and not line.startswith('+++'):
                patch_lines.append(i)
        patch_line_str = ', '.join(map(str, patch_lines))
        return f"""아래는 GitHub Pull Request의 diff patch입니다.

- patch의 각 줄에서 +로 시작하는 줄(즉, 실제로 변경/추가된 코드)에만 코멘트를 달아주세요.
- 반드시 아래 patch에서 +로 시작하는 줄의 라인 번호({patch_line_str})만 사용하세요.
- patch에 없는 라인 번호는 절대 사용하지 마세요.
- 아래 예시와 완전히 동일한 양식으로만 작성하세요.
- 만약 코멘트가 없다면 'NO ISSUE'라고만 답하세요.

Line: [patch에서 +로 시작하는 줄의 실제 라인 번호]
Severity: [HIGH|MEDIUM|LOW]
Category: [BUG|PERFORMANCE|READABILITY|SECURITY|OTHER]
Description: [문제 설명]
Proposed Solution: [개선 방안]

예시:
Line: {patch_lines[0] if patch_lines else 1}
Severity: HIGH
Category: BUG
Description: This line has a potential bug
Proposed Solution: Fix the bug by doing X

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
                    "model": "codellama:34b",
                    "prompt": self._create_prompt(content),
                    "system": "한국어로 답하세요. 아래 양식 이외의 텍스트(요약, 인삿말, 기타 설명 등)는 한 글자도 쓰지 마세요. 반드시 아래 예시와 완전히 동일한 양식으로만 작성하세요. Line: ...으로 시작하지 않는 문장은 절대 쓰지 마세요. 만약 코멘트가 없다면 'NO ISSUE'라고만 답하세요.",
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
        """PR의 코드를 리뷰 (파일별 summary만 생성)"""
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
                        # 파일별 summary만 남김
                        review_results.append({
                            'file': result['file'],
                            'summary': result['review']
                        })

            return {
                'pr_number': pr_data.get('number', ''),
                'title': pr_data.get('title', ''),
                'file_summaries': review_results
            }

        except Exception as e:
            logger.error(f"코드 리뷰 중 오류 발생: {str(e)}")
            raise

    def post_review(self, pr_number: str, summary: str, line_comments: List[Dict[str, Any]]) -> None:
        """리뷰 결과를 GitHub PR에 포스팅합니다."""
        try:
            logger.debug(f"[DEBUG] post_review 진입: summary={summary}")
            logger.debug(f"[DEBUG] 전체 line_comments: {line_comments}")
            
            review_comments = []
            for comment in line_comments:
                try:
                    logger.debug(f"[DEBUG] 원본 comment['line']: {comment['line']}")
                    logger.debug(f"[DEBUG] comment['file']: {comment['file']}")
                    
                    # 파일의 patch 가져오기
                    file_patch = self._get_file_patch(pr_number, comment['file'])
                    if not file_patch:
                        logger.warning(f"파일 patch를 찾을 수 없음: {comment['file']}")
                        continue
                    
                    logger.debug(f"[DEBUG] patch 내용 (앞 20줄):\n{file_patch[:1000]}")
                    
                    # 라인 번호를 position으로 변환
                    line_to_position = self._create_line_to_position_mapping(file_patch)
                    logger.debug(f"[DEBUG] line_to_position 매핑: {line_to_position}")
                    
                    # 라인 번호 파싱
                    lines = self._parse_line_numbers(comment['line'])
                    logger.debug(f"[DEBUG] 파싱된 라인 리스트: {lines}")
                    
                    for line in lines:
                        if line in line_to_position:
                            position = line_to_position[line]
                            logger.debug(f"[DEBUG] 파일: {comment['file']}, 라인: {line}, position: {position}")
                            
                            # 코멘트 생성
                            review_comment = {
                                'path': comment['file'],
                                'position': position,
                                'body': comment['body']  # 여기서 body를 사용
                            }
                            review_comments.append(review_comment)
                        else:
                            logger.warning(f"라인 {line}에 대한 position을 찾을 수 없음")
                
                except Exception as e:
                    logger.warning(f"Error creating comment: {str(e)}")
                    continue
            
            logger.debug(f"[DEBUG] 최종 review_comments 전체: {review_comments}")
            
            # 리뷰 생성
            logger.info(f"[DEBUG] create_review 파라미터: summary={summary}, comments={review_comments}")
            self.repo.create_pull_request_review(
                pr_number,
                body=summary,
                event='COMMENT',
                comments=review_comments
            )
            
            if not review_comments:
                logger.info("Posted summary comment only (no line comments)")
            else:
                logger.info(f"Posted {len(review_comments)} line comments")
                
        except Exception as e:
            logger.error(f"리뷰 포스팅 중 오류 발생: {str(e)}")
            raise 