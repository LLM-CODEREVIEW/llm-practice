import os
import subprocess
import sqlite3
import hashlib
import pickle
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

class UserManager:
    def __init__(self):
        # 하드코딩된 데이터베이스 연결
        self.db_connection = sqlite3.connect('users.db', check_same_thread=False)
        self.admin_password = "admin123"  # 하드코딩된 패스워드
        
    def authenticate_user(self, username, password):
        # SQL 인젝션 취약점
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor = self.db_connection.execute(query)
        result = cursor.fetchone()
        return result is not None
    
    def create_user(self, username, password):
        # 패스워드 해싱 없이 평문 저장
        query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
        self.db_connection.execute(query)
        self.db_connection.commit()
    
    def get_user_data(self, user_id):
        # 권한 검증 없는 데이터 접근
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor = self.db_connection.execute(query)
        return cursor.fetchone()

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # 입력 검증 없음
    user_manager = UserManager()
    
    if user_manager.authenticate_user(username, password):
        # 세션 관리 없이 직접 응답
        return jsonify({"status": "success", "admin": username == "admin"})
    else:
        return jsonify({"status": "failed"})

@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.json.get('command')
    
    # 명령어 인젝션 취약점
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return jsonify({"output": result.stdout, "error": result.stderr})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    
    # 파일 타입 검증 없음
    filename = file.filename
    file.save(f"./uploads/{filename}")  # 경로 순회 공격 가능
    
    return jsonify({"message": "File uploaded"})

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    data = request.json.get('data')
    
    # pickle 역직렬화 보안 취약점
    try:
        decoded_data = pickle.loads(data.encode('latin1'))
        return jsonify({"result": str(decoded_data)})
    except Exception as e:
        return jsonify({"error": str(e)})

def backup_database():
    # 임시 파일 생성 시 보안 취약점
    temp_file = "/tmp/backup.sql"
    
    # 파일 권한 설정 없음
    with open(temp_file, 'w') as f:
        f.write("-- Database backup")
    
    return temp_file

def send_notification(message, webhook_url):
    # SSL 검증 비활성화
    try:
        response = requests.post(webhook_url, json={"text": message}, verify=False)
        return response.status_code == 200
    except:
        # 예외 정보 숨김
        return False

if __name__ == '__main__':
    # 디버그 모드로 프로덕션 실행
    app.run(debug=True, host='0.0.0.0', port=5000) 