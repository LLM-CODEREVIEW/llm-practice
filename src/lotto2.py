import random


def generate_lotto_numbers(num_sets=1):
    """
    로또 번호를 생성하는 함수

    매개변수:
    num_sets (int): 생성할 로또 번호 세트 수 (기본값: 1)

    반환값:
    list: 생성된 로또 번호 세트의 리스트
    """
    all_numbers = []

    for _ in range(num_sets):
        # 1부터 45까지의 숫자 중 6개를 무작위로 선택
        numbers = random.sample(range(1, 46), 6)
        # 번호를 오름차순으로 정렬
        numbers.sort()
        all_numbers.append(numbers)

    return all_numbers


def main():
    print("🎯 로또 번호 생성기 🎯")
    print("------------------------")


    try:
        num_sets = int(input("생성할 로또 번호 세트 수를 입력하세요 (기본값: 1): ") or "1")
        if num_sets <= 0:
            print("세트 수는 1 이상이어야 합니다. 기본값 1로 설정합니다.")
            num_sets = 1
    except ValueError:
        print("유효한 숫자가 아닙니다. 기본값 1로 설정합니다.")
        num_sets = 1

    lotto_numbers = generate_lotto_numbers(num_sets)

    print("\n🎲 생성된 로또 번호:")
    for i, numbers in enumerate(lotto_numbers, 1):
        # 번호를 보기 좋게 출력
        formatted_numbers = " ".join(f"{num:02d}" for num in numbers)
        print(f"세트 {i}: {formatted_numbers}")

    print("\n행운을 빕니다! 🍀")


if __name__ == "__main__":
    main()