# LLM 기반 GitHub PR 코드 리뷰 시스템

이 프로젝트는 CodeLlama 13B 모델을 활용하여 GitHub Pull Request에 대한 자동 코드 리뷰를 수행하는 시스템입니다.

## 주요 기능

- PR 생성/업데이트 시 자동 코드 리뷰
- 문제가 발견된 코드 라인에 인라인 코멘트 추가
- 전체 리뷰 요약 제공
- 다양한 프로그래밍 언어 지원

## 기술 스택

- Python 3.10+
- CodeLlama 13B
- GitHub API
- GitHub Actions

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

## 사용 방법

1. GitHub 저장소 설정
   - GitHub Actions 워크플로우 파일이 자동으로 PR 이벤트를 감지합니다.
   - 필요한 환경 변수를 GitHub 저장소의 Secrets에 설정합니다.

2. PR 생성
   - 새로운 PR을 생성하면 자동으로 코드 리뷰가 시작됩니다.
   - 리뷰 결과는 PR 코멘트와 인라인 코멘트로 표시됩니다.

## 환경 변수 설정

다음 환경 변수들을 GitHub Secrets에 설정해야 합니다:

- `GITHUB_TOKEN`: GitHub API 접근을 위한 토큰
- `HUGGINGFACE_TOKEN`: Hugging Face API 토큰 (CodeLlama 모델 접근용)

## 라이선스

MIT License 