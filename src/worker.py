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
