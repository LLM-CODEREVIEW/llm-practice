import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    print("경고: GITHUB_TOKEN이 설정되지 않았습니다. GitHub API 호출이 실패할 수 있습니다.")

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
if not WEBHOOK_SECRET:
    print("경고: WEBHOOK_SECRET이 설정되지 않았습니다. GitHub 웹훅 검증이 비활성화됩니다.")

# 서버 설정
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 8080))

# 디버그 모드
DEBUG = "TRUE"