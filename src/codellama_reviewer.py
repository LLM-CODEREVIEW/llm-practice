import requests
import json
from loguru import logger
from typing import Dict, List, Any, Optional
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
import subprocess
import atexit
import signal
import socket
import psutil
from prompt.xmlStyle import template
from sentence_transformers import SentenceTransformer
import chromadb


class CodeLlamaReviewer:
    def __init__(self, api_url: str, chroma_db_path: str = "./chroma_db"):
        logger.info("=== CodeLlamaReviewer 초기화 시작 ===")
        logger.info(f"입력된 api_url: {api_url}")

        self.original_api_url = api_url
        self.api_url = api_url
        self.ssh_process = None
        self.tunnel_port = 8080
        self.max_workers = 3
        
        # CodingConventionVerifier 관련 초기화
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        # ChromaDB 초기화
        logger.info("=== ChromaDB 초기화 시작 ===")
        try:
            # 클라이언트 생성
            self.client = chromadb.PersistentClient(
                path=chroma_db_path,
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
        except Exception as e:
            logger.error(f"ChromaDB 초기화 실패: {str(e)}")
            raise

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

    def _detect_language(self, code: str) -> str:
        """코드에서 언어를 감지합니다."""
        if ".java" in code:
            return "java"
        elif ".swift" in code:
            return "swift"
        return "java"  # 기본값

    # FIXME: LLM 모델 바꿔보기
    def _call_ollama_api(self, prompt: str, model: str = "qwen2.5-coder:32b-instruct") -> str:
        """Ollama API를 호출하여 응답을 받아옵니다."""
        logger.info(f"=== Ollama API 호출 시작 ===")
        logger.info(f"API URL: {self.api_url}/api/generate")
        logger.info(f"요청 모델: {model}")
        logger.info(f"프롬프트 길이: {len(prompt)} characters")
        
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "system": """
    You are a senior developer proficient in iOS and backend.

    - Always generate your review **in Korean only**, even if this prompt is written in English.
    - Do **not copy** any example content from the <output-format> section. It is for structure only.
    - The review must be based solely on the <diff> section.
    - Detect all code issues first, then group them by severity level in the final output.
            """
        }

        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=request_data,
                timeout=300,  # 5분 타임아웃
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'CodeReview-Bot/1.0'
                }
            )

            logger.info(f"ollama API response: {response.json()}")

            if response.status_code != 200:
                logger.error(f"=== API 호출 실패 상세 정보 ===")
                logger.error(f"상태 코드: {response.status_code}")
                logger.error(f"응답 헤더: {dict(response.headers)}")
                logger.error(f"응답 내용: {response.text}")
                logger.error(f"요청 URL: {response.url}")
                raise Exception(f"Ollama API 호출 실패: {response.status_code}")
            else:
                print(response.status_code, response.text)
            result = response.json()
            return result.get('response', '')

        except requests.exceptions.Timeout as e:
            logger.error(f"API 요청 타임아웃: {str(e)}")
            raise Exception("Ollama API 요청 타임아웃")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API 연결 오류: {str(e)}")
            raise Exception(f"Ollama API 연결 오류: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류: {str(e)}")
            raise Exception(f"Ollama API 요청 오류: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama API 호출 중 예상치 못한 오류: {str(e)}")
            raise

    def _get_convention_guide(self, code: str) -> str:
        """코드에 대한 코딩 컨벤션 가이드를 검색합니다."""
        try:
        # 1. 언어 감지 및 룰 로딩
            detected_language = self._detect_language(code)
            if detected_language not in ["java", "swift"]:
                logger.warning(f"지원되지 않는 언어: {detected_language}")
                return "not applicable"

            json_path = f"{detected_language}_style_rules.json"
            with open(json_path, encoding="utf-8") as f:
                style_rules = json.load(f)[f"{detected_language}_style_guide_rules"]

            collection_name = f"{detected_language}_style_rules"
            try:
                collection = self.client.get_collection(collection_name)
            except Exception as e:
                logger.warning(f"VectorDB 컬렉션 '{collection_name}' 로드 실패: {e}")
                return "not applicable"

            results = []
        
            for rule in style_rules:
                rule_text = rule["rule"]

            # 2. LLM에게 위반 여부 판단 요청
                prompt = f"""
You are a code style reviewer.
Please check if the following code diff violates this coding convention rule.

📘 Rule:
\"\"\"
{rule_text}
\"\"\"

🧾 Code Diff:
\"\"\"
{code}
\"\"\"

If the rule is clearly violated, return only: YES  
If not violated or ambiguous, return only: NO
"""

                try:
                    llm_response = self._call_ollama_api(prompt).strip().upper()
                    if llm_response == "YES":
                    # 3. VectorDB에서 해당 룰 설명 보강
                        query = f"{rule['title']} - {rule_text}"
                        vec = self.model.encode(query).tolist()
                        vdb_results = collection.query(query_embeddings=[vec], n_results=1)

                        explanation = ""
                        if vdb_results["documents"] and vdb_results["metadatas"]:
                            doc = vdb_results["documents"][0][0]
                            meta = vdb_results["metadatas"][0][0]
                            explanation = f"- [{meta['category']}] {doc.strip()}"
                        else:
                            explanation = f"- [{rule['category']}] {rule['title']}: {rule_text}"

                        results.append(explanation)
                except Exception as e:
                    logger.error(f"LLM 판단 중 오류 발생 (rule ID: {rule.get('id')}): {e}")
                    continue
            return "\n".join(results) if results else "not applicable"

        except Exception as e:
            logger.error(f"컨벤션 가이드 생성 실패: {e}")
            return "not applicable"

    def _export_json_array(self, text: str) -> list:
        """텍스트에서 JSON 배열을 추출합니다."""
        match = re.search(r"\[\s*\".*?\"\s*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return []

    def _create_prompt(self, code: str) -> str:
        """코드 리뷰를 위한 프롬프트를 생성합니다."""
        if not code:
            logger.warning("입력된 코드가 비어있습니다.")
            return ""

        try:
            convention_guide = self._get_convention_guide(code)
            logger.info(f"_get_convention_guide 결과 {convention_guide}")
            
            # xmlStyle.py의 템플릿 사용
            if not hasattr(template, 'replace'):
                logger.error("template이 올바른 형식이 아닙니다.")
                return code

            final_prompt = (
                template
                .replace("{{CONVENTION_GUIDE_PLACEHOLDER}}", convention_guide or "not applicable")
                .replace("{{PR_DIFF_PLACEHOLDER}}", code.strip())
            )

            return final_prompt
        except Exception as e:
            logger.error(f"프롬프트 생성 중 오류 발생: {str(e)}")
            return code  # 오류 발생 시 원본 코드 반환

    def review_code(self, pr_data: str) -> str:
        """PR의 코드를 리뷰하고 결과를 문자열로 반환합니다."""
        logger.info("=== 코드 리뷰 시작 ===")

        if not pr_data:
            logger.warning("PR 데이터가 비어있습니다.")
            return "NO ISSUE"

        try:
            # Ollama API 호출
            prompt = self._create_prompt(pr_data)
            if not prompt:
                logger.warning("생성된 프롬프트가 비어있습니다.")
                return "NO ISSUE"
            
            review_text = self._call_ollama_api(prompt)
            
            if not review_text:
                logger.warning("리뷰 결과가 비어있습니다.")
                return "NO ISSUE"
            
            logger.info(f"리뷰 완료 (텍스트 길이: {len(review_text)} characters)")
            return review_text

        except Exception as e:
            logger.error(f"코드 리뷰 중 오류 발생: {str(e)}")
            return "리뷰 중 오류가 발생했습니다. 다시 시도해주세요."

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

