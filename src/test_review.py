import os
import sys
from typing import List, Dict, Any
import json
import requests
from datetime import datetime


class DataProcessor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.processed_data = []
        self._validate_data()

    def _validate_data(self):
        """데이터 유효성 검사"""
        if not isinstance(self.data, list):
            raise ValueError("데이터는 리스트여야 합니다")

        for item in self.data:
            if not isinstance(item, dict):
                raise ValueError("각 항목은 딕셔너리여야 합니다")

    def process_data(self) -> List[Dict[str, Any]]:
        """데이터 처리"""
        try:
            for item in self.data:
                # 중복 키 체크 없음
                processed_item = {
                    'id': item.get('id', 0),
                    'name': item.get('name', ''),
                    'value': item.get('value', 0),
                    'timestamp': datetime.now().isoformat()
                }
                self.processed_data.append(processed_item)

            return self.processed_data
        except Exception as e:
            print(f"에러 발생: {str(e)}")  # 로깅 대신 print 사용
            return []

    def save_to_file(self, filename: str):
        """처리된 데이터를 파일로 저장"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.processed_data, f)
        except Exception as e:
            print(f"파일 저장 실패: {str(e)}")


def main():
    # 하드코딩된 데이터
    test_data = [
        {'id': 1, 'name': 'test1', 'value': 100},
        {'id': 2, 'name': 'test2', 'value': 200}
    ]

    processor = DataProcessor(test_data)
    result = processor.process_data()

    # 결과 출력
    print(result)

    # 파일 저장
    processor.save_to_file('output.json')


if __name__ == '__main__':
    main()