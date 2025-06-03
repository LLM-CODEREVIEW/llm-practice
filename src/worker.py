import json
import re
import subprocess

# JSON 배열만 추출
def export_json_array(text):
    # JSON 배열을 찾기 위한 더 유연한 정규식
    match = re.search(r"\[\s*[\"'].*?[\"']\s*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 다른 시도
            try:
                # 따옴표를 이스케이프 처리
                escaped = match.group(0).replace("'", '"')
                return json.loads(escaped)
            except json.JSONDecodeError:
                pass
    return []

# Java/Swift 언어 판별(코딩컨벤션 VectorDB 참조용)
def detect_language(code):
    # Swift 코드 특징
    swift_patterns = [
        r'class\s+\w+:\s*UIViewController',
        r'func\s+\w+\s*\(',
        r'@IBAction',
        r'override\s+func',
        r'var\s+\w+:',
        r'let\s+\w+:',
    ]
    
    # Java 코드 특징
    java_patterns = [
        r'public\s+class\s+\w+',
        r'private\s+class\s+\w+',
        r'@Override',
        r'public\s+void\s+\w+\s*\(',
        r'private\s+void\s+\w+\s*\(',
        r'String\s+\w+',
    ]
    
    swift_matches = sum(1 for pattern in swift_patterns if re.search(pattern, code))
    java_matches = sum(1 for pattern in java_patterns if re.search(pattern, code))
    
    return "swift" if swift_matches > java_matches else "java"

