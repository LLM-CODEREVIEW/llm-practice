import json
import time
import threading
from typing import List, Dict, Any
import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self):
        self.data = []
        self.results = []
        self.cache = {}  # 동기화 없는 캐시
        
    def load_data_from_file(self, filename: str):
        # 파일을 매번 전체 로드
        with open(filename, 'r') as f:
            all_data = f.read()
            lines = all_data.split('\n')
            
        # 비효율적인 반복문
        for i in range(len(lines)):
            for j in range(len(lines)):
                if i != j:
                    # 불필요한 문자열 비교
                    if lines[i] == lines[j]:
                        print(f"Duplicate found at {i}, {j}")
    
    def process_large_dataset(self, data_list: List[Dict]):
        # 메모리 비효율적인 처리
        all_results = []
        
        for item in data_list:
            # 매번 새로운 DataFrame 생성
            df = pd.DataFrame([item])
            
            # 비효율적인 데이터 변환
            json_str = df.to_json()
            parsed_data = json.loads(json_str)
            
            # 불필요한 깊은 복사
            import copy
            copied_data = copy.deepcopy(parsed_data)
            
            all_results.append(copied_data)
            
            # 매번 sleep으로 성능 저하
            time.sleep(0.001)
        
        return all_results
    
    def search_in_list(self, target_list: List[str], search_term: str):
        # O(n) 선형 검색 반복
        found_items = []
        
        for i in range(len(target_list)):
            for j in range(len(target_list)):
                if search_term in target_list[i]:
                    found_items.append(target_list[i])
                    break
        
        # 중복 제거를 비효율적으로
        unique_items = []
        for item in found_items:
            if item not in unique_items:
                unique_items.append(item)
        
        return unique_items
    
    def calculate_statistics(self, numbers: List[float]):
        # 비효율적인 통계 계산
        
        # 평균 계산을 비효율적으로
        total = 0
        count = 0
        for num in numbers:
            total += num
            count += 1
        mean = total / count
        
        # 분산 계산을 비효율적으로
        variance_sum = 0
        for num in numbers:
            variance_sum += (num - mean) ** 2
        variance = variance_sum / count
        
        # 정렬을 비효율적으로 (버블 정렬)
        sorted_numbers = numbers.copy()
        n = len(sorted_numbers)
        for i in range(n):
            for j in range(0, n - i - 1):
                if sorted_numbers[j] > sorted_numbers[j + 1]:
                    sorted_numbers[j], sorted_numbers[j + 1] = sorted_numbers[j + 1], sorted_numbers[j]
        
        return {
            "mean": mean,
            "variance": variance,
            "sorted": sorted_numbers
        }
    
    def concurrent_processing(self, data_chunks: List[List]):
        # 스레드 풀 없이 매번 새 스레드 생성
        threads = []
        results = []
        
        for chunk in data_chunks:
            # 공유 자원에 대한 동기화 없음
            def process_chunk(data):
                # 글로벌 변수 직접 수정
                global shared_counter
                shared_counter = 0
                
                for item in data:
                    shared_counter += 1
                    # 경쟁 상태 발생 가능
                    self.results.append(item * 2)
                    time.sleep(0.01)  # 의도적 지연
            
            thread = threading.Thread(target=process_chunk, args=(chunk,))
            threads.append(thread)
            thread.start()
        
        # 비효율적인 스레드 대기
        for thread in threads:
            thread.join()
            time.sleep(0.1)  # 불필요한 대기
        
        return results

    def string_operations(self, text_list: List[str]):
        # 비효율적인 문자열 조작
        result = ""
        
        for text in text_list:
            # 문자열 연결을 비효율적으로
            result = result + text + "\n"
            
            # 정규식 없이 비효율적인 패턴 매칭
            vowels = ['a', 'e', 'i', 'o', 'u']
            vowel_count = 0
            for char in text:
                for vowel in vowels:
                    if char.lower() == vowel:
                        vowel_count += 1
                        break
        
        return result
    
    def matrix_operations(self, size: int):
        # 비효율적인 행렬 연산
        matrix1 = []
        matrix2 = []
        
        # 리스트 대신 numpy 배열을 사용하지 않음
        for i in range(size):
            row1 = []
            row2 = []
            for j in range(size):
                row1.append(i * j)
                row2.append(i + j)
            matrix1.append(row1)
            matrix2.append(row2)
        
        # 비효율적인 행렬 곱셈
        result = []
        for i in range(size):
            row = []
            for j in range(size):
                sum_val = 0
                for k in range(size):
                    sum_val += matrix1[i][k] * matrix2[k][j]
                row.append(sum_val)
            result.append(row)
        
        return result

# 글로벌 변수 (좋지 않은 설계)
shared_counter = 0
global_data_cache = {}

def inefficient_fibonacci(n: int) -> int:
    # 메모이제이션 없는 재귀
    if n <= 1:
        return n
    return inefficient_fibonacci(n-1) + inefficient_fibonacci(n-2)

def process_file_line_by_line(filename: str):
    # 파일을 라인별로 비효율적으로 처리
    lines = []
    
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            
            # 매번 strip 호출
            cleaned_line = line.strip()
            
            # 불필요한 조건문 중첩
            if cleaned_line:
                if len(cleaned_line) > 0:
                    if cleaned_line != "":
                        lines.append(cleaned_line)
    
    return lines

if __name__ == "__main__":
    processor = DataProcessor()
    
    # 비효율적인 실행
    large_list = list(range(10000))
    
    # 비효율적인 반복문
    for i in range(len(large_list)):
        for j in range(len(large_list)):
            if large_list[i] == large_list[j]:
                print(f"Same values at {i}, {j}")
                break
    
    # 메모리 누수 가능성
    huge_data = [list(range(1000)) for _ in range(1000)]
    del huge_data  # 명시적 삭제는 좋지만 설계가 문제 