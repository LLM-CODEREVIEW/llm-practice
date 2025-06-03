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
import socket
import psutil


class CodeLlamaReviewer:
    def __init__(self, api_url: str):
        logger.info("=== CodeLlamaReviewer 초기화 시작 ===")
        logger.info(f"입력된 api_url: {api_url}")

        self.original_api_url = api_url
        self.api_url = api_url
        self.ssh_process = None
        self.tunnel_port = 8080
        self.max_workers = 3

        # 환경 변수 확인
        self._log_environment_variables()

        # SSH 터널 설정 (필요한 경우만)
        if self._should_use_ssh_tunnel():
            self._setup_ssh_tunnel()
        else:
            logger.info("SSH 터널링 불필요 - 직접 API 호출 사용")

        # Ollama 연결 확인
        self._check_ollama()

        logger.info("=== CodeLlamaReviewer 초기화 완료 ===")

    def _log_environment_variables(self):
        """환경 변수 상태 로깅"""
        logger.info("=== 환경 변수 확인 ===")
        env_vars = ['LLM_SERVER_HOST', 'LLM_SERVER_USER', 'LLM_SERVER_PORT']

        for var in env_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"{var}: {value}")
            else:
                logger.warning(f"{var}: 설정되지 않음")

        # SSH 에이전트 상태 확인
        ssh_auth_sock = os.getenv('SSH_AUTH_SOCK')
        if ssh_auth_sock:
            logger.info(f"SSH_AUTH_SOCK: {ssh_auth_sock}")
        else:
            logger.warning("SSH_AUTH_SOCK: 설정되지 않음")

    def _should_use_ssh_tunnel(self) -> bool:
        """SSH 터널링이 필요한지 판단"""
        # localhost나 127.0.0.1이 아니고, 환경 변수가 설정되어 있으면 SSH 터널 사용
        is_local = any(host in self.original_api_url.lower() for host in ['localhost', '127.0.0.1'])
        has_ssh_config = all(os.getenv(var) for var in ['LLM_SERVER_HOST', 'LLM_SERVER_USER'])

        logger.info(f"API URL이 로컬인가? {is_local}")
        logger.info(f"SSH 설정이 있는가? {has_ssh_config}")

        return not is_local and has_ssh_config

    def _setup_ssh_tunnel(self):
        """SSH 터널을 설정합니다."""
        logger.info("=== SSH 터널 설정 시작 ===")

        try:
            # 환경 변수 가져오기
            host = os.getenv('LLM_SERVER_HOST')
            user = os.getenv('LLM_SERVER_USER')
            port = os.getenv('LLM_SERVER_PORT', '22')

            logger.info(f"SSH 연결 정보: {user}@{host}:{port}")

            if not all([host, user]):
                logger.error("SSH 연결에 필요한 환경 변수가 설정되지 않았습니다.")
                logger.error(f"LLM_SERVER_HOST: {host}")
                logger.error(f"LLM_SERVER_USER: {user}")
                raise ValueError("Missing required environment variables for SSH connection")

            # SSH 연결 테스트 먼저 수행
            if not self._test_ssh_connection(host, user, port):
                raise Exception("SSH 연결 테스트 실패")

            # SSH 터널 포트 사용 가능 여부 확인
            if not self._is_port_available(self.tunnel_port):
                logger.warning(f"포트 {self.tunnel_port}가 이미 사용 중입니다. 다른 포트를 찾는 중...")
                self.tunnel_port = self._find_available_port()
                logger.info(f"사용할 포트: {self.tunnel_port}")

            # SSH 터널 명령어 구성
            ssh_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ConnectTimeout=30',
                '-o', 'ServerAliveInterval=60',
                '-o', 'ServerAliveCountMax=3',
                '-N',  # 원격 명령 실행 안함
                '-f',  # 백그라운드 실행
                '-L', f'{self.tunnel_port}:localhost:11434',  # 로컬 포트 포워딩
                '-p', str(port),
                f'{user}@{host}'
            ]

            logger.info(f"SSH 터널 명령어: {' '.join(ssh_cmd)}")

            # SSH 터널 실행
            logger.info("SSH 터널 프로세스 시작...")
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            logger.info(f"SSH 터널 반환 코드: {result.returncode}")
            if result.stdout:
                logger.info(f"SSH stdout: {result.stdout}")
            if result.stderr:
                logger.info(f"SSH stderr: {result.stderr}")

            if result.returncode != 0:
                logger.error("SSH 터널 생성 실패")
                raise Exception(f'SSH 터널 생성 실패: {result.stderr}')

            # SSH 터널 프로세스 찾기 및 저장
            self._find_and_store_ssh_process()

            # 터널 연결 대기 및 확인
            logger.info("SSH 터널 연결 대기 중...")
            max_wait = 30
            for i in range(max_wait):
                if self._check_tunnel_connection():
                    logger.info(f"SSH 터널 연결 성공! (대기 시간: {i + 1}초)")
                    break
                time.sleep(1)
                if i % 5 == 4:  # 5초마다 로그
                    logger.info(f"터널 연결 대기 중... ({i + 1}/{max_wait}초)")
            else:
                raise Exception('SSH 터널 연결 확인 실패 - 타임아웃')

            # API URL을 터널 포인트로 변경
            self.api_url = f"http://localhost:{self.tunnel_port}"
            logger.info(f"API URL이 {self.api_url}로 변경되었습니다.")

            # 프로세스 종료 시 SSH 터널도 종료되도록 설정
            atexit.register(self._cleanup_ssh_tunnel)
            signal.signal(signal.SIGTERM, self._cleanup_ssh_tunnel)

            logger.info("SSH 터널이 성공적으로 설정되었습니다.")

        except subprocess.TimeoutExpired:
            logger.error("SSH 터널 생성 타임아웃 (60초)")
            raise Exception('SSH 연결 타임아웃')
        except Exception as e:
            logger.error(f"SSH 터널 설정 중 오류 발생: {str(e)}")
            self._cleanup_ssh_tunnel()
            raise Exception(f'SSH 연결 실패: {str(e)}')

    def _test_ssh_connection(self, host: str, user: str, port: str) -> bool:
        """SSH 연결 테스트"""
        logger.info("=== SSH 연결 테스트 시작 ===")

        try:
            ssh_test_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ConnectTimeout=15',
                '-o', 'BatchMode=yes',  # 인터랙티브 입력 방지
                '-p', str(port),
                f'{user}@{host}',
                'echo "SSH 연결 테스트 성공"'
            ]

            logger.info(f"SSH 테스트 명령어: {' '.join(ssh_test_cmd)}")

            result = subprocess.run(
                ssh_test_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            logger.info(f"SSH 테스트 반환 코드: {result.returncode}")
            logger.info(f"SSH 테스트 stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"SSH 테스트 stderr: {result.stderr}")

            if result.returncode == 0:
                logger.info("SSH 연결 테스트 성공!")
                return True
            else:
                logger.error("SSH 연결 테스트 실패")
                return False

        except subprocess.TimeoutExpired:
            logger.error("SSH 연결 테스트 타임아웃")
            return False
        except Exception as e:
            logger.error(f"SSH 연결 테스트 중 예외 발생: {str(e)}")
            return False

    def _is_port_available(self, port: int) -> bool:
        """포트 사용 가능 여부 확인"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.bind(('localhost', port))
                return True
        except OSError:
            return False

    def _find_available_port(self) -> int:
        """사용 가능한 포트 찾기"""
        for port in range(8080, 8100):
            if self._is_port_available(port):
                return port
        raise Exception("사용 가능한 포트를 찾을 수 없습니다")

    def _find_and_store_ssh_process(self):
        """SSH 터널 프로세스 찾기 및 저장"""
        try:
            logger.info("SSH 터널 프로세스 검색 중...")

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if ('ssh' in proc.info['name'].lower() and
                            f'{self.tunnel_port}:localhost:11434' in cmdline and
                            os.getenv('LLM_SERVER_HOST') in cmdline):
                        self.ssh_process = proc
                        logger.info(f"SSH 터널 프로세스 발견: PID {proc.info['pid']}")
                        logger.info(f"명령어: {cmdline}")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not self.ssh_process:
                logger.warning("SSH 터널 프로세스를 찾을 수 없습니다")

        except Exception as e:
            logger.warning(f"SSH 프로세스 검색 중 오류: {str(e)}")

    def _check_tunnel_connection(self) -> bool:
        """터널 연결 상태 확인"""
        try:
            logger.debug(f"터널 연결 확인: localhost:{self.tunnel_port}")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                result = sock.connect_ex(('localhost', self.tunnel_port))

                if result == 0:
                    logger.debug("터널 포트 연결 성공")
                    return True
                else:
                    logger.debug(f"터널 포트 연결 실패: {result}")
                    return False

        except Exception as e:
            logger.debug(f"터널 연결 확인 중 예외: {str(e)}")
            return False

    def _cleanup_ssh_tunnel(self, *args):
        """SSH 터널을 정리합니다."""
        logger.info("=== SSH 터널 정리 시작 ===")

        try:
            if self.ssh_process:
                logger.info(f"SSH 프로세스 종료 중: PID {self.ssh_process.pid}")
                self.ssh_process.terminate()

                # 프로세스가 종료될 때까지 대기 (최대 5초)
                try:
                    self.ssh_process.wait(timeout=5)
                    logger.info("SSH 프로세스 정상 종료")
                except psutil.TimeoutExpired:
                    logger.warning("SSH 프로세스 강제 종료")
                    self.ssh_process.kill()

                self.ssh_process = None

            # 추가로 SSH 터널 프로세스 검색 및 종료
            logger.info("남은 SSH 터널 프로세스 검색 중...")
            killed_count = 0

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if ('ssh' in proc.info['name'].lower() and
                            f'{self.tunnel_port}:localhost:11434' in cmdline):
                        logger.info(f"남은 SSH 터널 프로세스 종료: PID {proc.info['pid']}")
                        proc.terminate()
                        killed_count += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.info(f"SSH 터널 정리 완료 (종료된 프로세스: {killed_count}개)")

        except Exception as e:
            logger.error(f"SSH 터널 정리 중 오류: {str(e)}")

    def _check_ollama(self):
        """Ollama API 서버 연결 확인"""
        logger.info("=== Ollama API 연결 확인 시작 ===")
        logger.info(f"API URL: {self.api_url}")

        max_retries = 3

        for attempt in range(max_retries):
            try:
                logger.info(f"Ollama 연결 시도 {attempt + 1}/{max_retries}")

                response = requests.get(
                    f"{self.api_url}/api/tags",
                    timeout=10
                )

                logger.info(f"응답 상태 코드: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    logger.info(f"사용 가능한 모델 수: {len(models)}")

                    for model in models:
                        model_name = model.get('name', 'Unknown')
                        model_size = model.get('size', 0)
                        logger.info(f"  - {model_name} (크기: {model_size:,} bytes)")

                    logger.info("Ollama API 서버 연결 성공!")
                    return
                else:
                    logger.error(f"Ollama API 응답 오류: {response.status_code}")
                    logger.error(f"응답 내용: {response.text}")

            except requests.exceptions.ConnectError as e:
                logger.error(f"Ollama 연결 오류 (시도 {attempt + 1}): {str(e)}")
            except requests.exceptions.Timeout as e:
                logger.error(f"Ollama 연결 타임아웃 (시도 {attempt + 1}): {str(e)}")
            except Exception as e:
                logger.error(f"Ollama 연결 중 예외 발생 (시도 {attempt + 1}): {str(e)}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.info(f"{wait_time}초 후 재시도...")
                time.sleep(wait_time)

        logger.error("Ollama API 서버 연결 실패 - 모든 재시도 완료")
        raise Exception("Ollama API 서버에 연결할 수 없습니다")

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
            description_match = re.search(r'(?:Description|설명):\s*(.*?)(?=\n(?:Proposed Solution|제안):|\Z)', block,
                                          re.DOTALL)
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

        logger.info(f"=== 파일 리뷰 시작: {filename} ===")

        if not content:
            logger.warning(f"파일 내용이 비어있습니다: {filename}")
            return None

        start_time = time.time()

        try:
            # Ollama API 호출
            logger.info(f"Ollama API 호출 중: {self.api_url}/api/generate")

            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": "codellama:34b",
                    "prompt": self._create_prompt(content),
                    "system": "한국어로 답하세요. 아래 양식 이외의 텍스트(요약, 인삿말, 기타 설명 등)는 한 글자도 쓰지 마세요. 반드시 아래 예시와 완전히 동일한 양식으로만 작성하세요. Line: ...으로 시작하지 않는 문장은 절대 쓰지 마세요. 만약 코멘트가 없다면 'NO ISSUE'라고만 답하세요.",
                    "stream": False
                },
                timeout=300  # 5분 타임아웃
            )

            logger.info(f"API 응답 상태 코드: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"API 호출 실패: {response.status_code}")
                logger.error(f"응답 내용: {response.text}")
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

            elapsed_time = time.time() - start_time
            logger.info(f"파일 {filename} 리뷰 완료 (소요시간: {elapsed_time:.2f}초)")

            return {
                'file': filename,
                'review': review_text,
                'comments': parsed_comments
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"파일 {filename} 리뷰 중 API 요청 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"파일 {filename} 리뷰 중 오류 발생: {str(e)}")
            return None

    def review_code(self, pr_data: dict) -> dict:
        """PR의 코드를 리뷰 (파일별 summary만 생성)"""
        logger.info("=== 코드 리뷰 시작 ===")

        try:
            review_results = []
            changed_files = pr_data.get('changed_files', [])

            logger.info(f"리뷰할 파일 수: {len(changed_files)}")
            for i, file_data in enumerate(changed_files):
                logger.info(f"  {i + 1}. {file_data.get('filename', 'Unknown')}")

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

            logger.info(f"리뷰 완료된 파일 수: {len(review_results)}")

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
        logger.info(f"=== 리뷰 포스팅 시작: PR #{pr_number} ===")

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

    def __del__(self):
        """소멸자에서 SSH 터널 정리"""
        self._cleanup_ssh_tunnel()