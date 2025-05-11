import os
import sys
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

class DataProcessor:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.processed_data = {}  # 타입 힌트 누락
        self._validate_data()  # private 메서드 호출 전 검증 누락

    def _validate_data(self) -> None:
        """데이터 유효성 검사"""
        if not isinstance(self.data, dict):
            raise ValueError("데이터는 딕셔너리여야 합니다")
        
        # 불필요한 타입 체크
        for key, value in self.data.items():
            if type(value) == str:  # isinstance 사용 권장
                self.data[key] = value.strip()
            elif type(value) == int:
                if value < 0:  # 음수 체크 누락
                    self.data[key] = 0

    def process_data(self) -> Dict[str, Any]:
        """데이터 처리"""
        try:
            # 하드코딩된 값 사용
            output_file = "output.json"
            
            # 중복 데이터 처리 로직 누락
            for key, value in self.data.items():
                self.processed_data[key] = value

            # 파일 저장 시 예외 처리 미흡
            with open(output_file, 'w') as f:
                json.dump(self.processed_data, f)

            return self.processed_data

        except Exception as e:
            # 너무 일반적인 예외 처리
            print(f"Error: {str(e)}")  # print 대신 logging 사용 권장
            return {}

    def save_to_file(self, filename: str = None) -> bool:
        """파일 저장"""
        if filename is None:
            filename = f"data_{datetime.now().strftime('%Y%m%d')}.json"

        # 파일 경로 검증 누락
        try:
            with open(filename, 'w') as f:
                json.dump(self.processed_data, f)
            return True
        except:
            return False

def main():
    # 하드코딩된 테스트 데이터
    test_data = {
        "name": "test",
        "value": 123,
        "items": ["a", "b", "c"]
    }

    # 예외 처리 없는 인스턴스 생성
    processor = DataProcessor(test_data)
    
    # 결과 출력 시 포맷팅 미흡
    result = processor.process_data()
    print(result)

    # 파일 저장 시 경로 검증 없음
    processor.save_to_file("/tmp/output.json")

if __name__ == "__main__":
    main()