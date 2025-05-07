from flask import Flask, request, jsonify
import hmac
import hashlib
import json
from config import WEBHOOK_SECRET, HOST, PORT, DEBUG
from pr_processor import process_pull_request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """GitHub 웹훅 이벤트 처리"""
    # 서명 검증
    signature = request.headers.get('X-Hub-Signature-256')
    if WEBHOOK_SECRET and not verify_signature(request.data, signature):
        return jsonify({"error": "잘못된 서명"}), 401

    # 이벤트 타입 확인
    event_type = request.headers.get('X-GitHub-Event')
    data = request.json

    # PR 이벤트만 처리
    if event_type == 'pull_request':
        action = data.get('action')

        # PR이 열리거나 업데이트된 경우만 처리
        if action in ['opened', 'synchronize']:
            pr_data = data.get('pull_request')
            repo_name = data.get('repository').get('full_name')
            pr_number = pr_data.get('number')

            print(f"PR 이벤트 감지: {repo_name}의 PR #{pr_number}, 액션: {action}")

            # 실제 환경에서는 백그라운드 작업으로 처리 (Celery 등)
            # 여기서는 간단히 직접 호출 (테스트용)
            process_pull_request(repo_name, pr_number)

        return jsonify({"status": "처리 중"}), 202

    # 다른 이벤트는 무시
    return jsonify({"status": "무시됨"}), 200

def verify_signature(payload, signature):
    """웹훅 서명 검증"""
    if not signature or not WEBHOOK_SECRET:
        return False

    expected_signature = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)

# 테스트용 경로
@app.route('/', methods=['GET'])
def index():
    return "GitHub 코드 리뷰 웹훅 서버가 실행 중입니다."
