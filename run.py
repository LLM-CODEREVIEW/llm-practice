from webhook_server import app
from config import HOST, PORT, DEBUG, GITHUB_TOKEN, WEBHOOK_SECRET

def check_configuration():
    """설정이 올바른지 확인"""
    if not GITHUB_TOKEN:
        print("경고: GITHUB_TOKEN이 설정되지 않았습니다!")
        return False

    if not WEBHOOK_SECRET:
        print("경고: WEBHOOK_SECRET이 설정되지 않았습니다!")
        print("웹훅 서명 검증이 비활성화됩니다. 프로덕션 환경에서는 권장하지 않습니다.")

    return True

if __name__ == '__main__':
    print("GitHub 코드 리뷰 웹훅 서버 시작 중...")

    if check_configuration():
        print(f"서버 실행: http://{HOST}:{PORT}")
        app.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        print("설정 오류로 서버를 시작할 수 없습니다. config.py 파일을 확인하세요.")