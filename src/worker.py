import json
import re
import subprocess

# JSON 배열만 추출
def export_json_array(text):
    match = re.search(r"\[\s*\".*?\"\s*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return []

# ollama 실행
def run_ollama(prompt: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ollama", "run", "llama3.2:latest"], #FIXME: LLM 모델 변경
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90
    )

# 코딩컨벤션 키워드 도출을 위한 프롬포트 질의
def get_convention_keyword_prompt(diff_input: str) -> str:
    return f"""
You are a senior developer reviewing code style.

Please analyze the following PR Diff and return any coding style violations you find
as a JSON array of short English sentences. Only include the JSON array in your response.
If there are no violations, return an empty array: []

PR Diff: {diff_input}
"""

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

