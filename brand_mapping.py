"""
브랜드 매핑 딕셔너리 (트랜잭션 지원)
key: 브랜드 이름, value: 브랜드 ID
동적으로 새로운 브랜드 처리 가능
JSON 파일로 데이터 저장/불러오기 지원
"""

import json
import os
from typing import Optional

# 브랜드 데이터 파일 경로
DEFAULT_DATA_FILE = "brand_data.json"
SQL_OUTPUT_FILE = "brand_sql.txt"

# 전역 변수
BRAND_NAME_TO_ID = {}
BRAND_ID_TO_NAME = {}
_current_max_id = 0
_id_sequence = 1

def _initialize_data():
    """데이터 초기화"""
    global BRAND_NAME_TO_ID, BRAND_ID_TO_NAME, _current_max_id, _id_sequence

    # JSON 파일에서 불러오기 시도
    if os.path.exists(DEFAULT_DATA_FILE):
        load_from_file(DEFAULT_DATA_FILE)
    else:
        # 파일이 없으면 빈 데이터로 시작
        BRAND_NAME_TO_ID = {}
        BRAND_ID_TO_NAME = {}
        _current_max_id = 0
        _id_sequence = 1
        print(f"'{DEFAULT_DATA_FILE}' 파일을 찾을 수 없습니다. 새로 생성합니다.")

def _update_sql_file(transaction=None):
    """
    전체 브랜드 목록으로 SQL 파일을 업데이트합니다.
    ID 포함하여 생성합니다.

    Args:
        transaction: FileTransaction 객체 (트랜잭션 사용 시)
    """
    try:
        sql_content = "INSERT INTO brands (id, name, is_deleted, created_at, updated_at) VALUES"

        all_brands = get_all_brands()
        sql_lines = []

        for name, id_val in all_brands:
            sql_line = f"({id_val}, '{name}', FALSE, NOW(), NOW())"
            sql_lines.append(sql_line)

        if sql_lines:
            sql_content += "\n" + ",\n".join(sql_lines) + ";"
        else:
            sql_content += ";"

        if transaction:
            # 트랜잭션 사용
            transaction.write_file(SQL_OUTPUT_FILE, sql_content)
        else:
            # 일반 파일 쓰기
            with open(SQL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(sql_content)

        print(f"SQL 파일이 업데이트되었습니다: {SQL_OUTPUT_FILE} (총 {len(all_brands)}개)")

    except Exception as e:
        print(f"SQL 파일 업데이트 중 오류: {e}")

def get_brand_id(brand_name: str, transaction=None) -> Optional[int]:
    """
    브랜드 이름으로 ID를 조회합니다.
    브랜드가 없으면 자동으로 새로 생성합니다.

    Args:
        brand_name (str): 브랜드 이름
        transaction: FileTransaction 객체 (트랜잭션 사용 시)

    Returns:
        int: 브랜드 ID (없으면 새로 생성하여 반환)
    """
    global _current_max_id, _id_sequence

    # 브랜드 이름 정리
    cleaned_name = brand_name.strip()

    # 빈 문자열 처리
    if not cleaned_name:
        return None

    # 기존 브랜드인 경우
    if cleaned_name in BRAND_NAME_TO_ID:
        return BRAND_NAME_TO_ID[cleaned_name]

    # 새로운 브랜드 자동 생성
    new_id = _id_sequence
    BRAND_NAME_TO_ID[cleaned_name] = new_id
    BRAND_ID_TO_NAME[new_id] = cleaned_name

    # 시퀀스 업데이트
    _id_sequence += 1
    _current_max_id = new_id

    print(f"새로운 브랜드 생성: '{cleaned_name}' -> ID: {new_id}")

    # SQL 파일 업데이트 (트랜잭션 또는 일반 파일 쓰기)
    _update_sql_file(transaction)

    # 변경사항 파일에 저장
    if transaction:
        # 트랜잭션 사용
        data = {
            'brands': BRAND_NAME_TO_ID,
            'next_id': _id_sequence
        }
        transaction.write_json(DEFAULT_DATA_FILE, data)
    else:
        # 일반 파일 쓰기
        save_to_file(DEFAULT_DATA_FILE)

    return new_id

def get_brand_name(brand_id: int) -> Optional[str]:
    """
    브랜드 ID로 이름을 조회합니다.

    Args:
        brand_id (int): 브랜드 ID

    Returns:
        str or None: 브랜드 이름 (존재하지 않으면 None)
    """
    return BRAND_ID_TO_NAME.get(brand_id)

def get_all_brands() -> list:
    """
    모든 브랜드 정보를 반환합니다.

    Returns:
        list of tuple: (브랜드 이름, 브랜드 ID) 리스트, ID순으로 정렬
    """
    return sorted([(name, id_val) for name, id_val in BRAND_NAME_TO_ID.items()],
                  key=lambda x: x[1])  # ID순으로 정렬

def get_brand_count() -> int:
    """
    총 브랜드 수를 반환합니다.

    Returns:
        int: 브랜드 수
    """
    return len(BRAND_NAME_TO_ID)

def get_next_brand_id() -> int:
    """
    다음에 생성될 브랜드 ID를 반환합니다.

    Returns:
        int: 다음 브랜드 ID
    """
    return _id_sequence

def save_to_file(filename: str = DEFAULT_DATA_FILE) -> bool:
    """
    브랜드 데이터를 JSON 파일로 저장합니다.

    Args:
        filename (str): 저장할 파일 이름

    Returns:
        bool: 성공 여부
    """
    try:
        data = {
            'brands': BRAND_NAME_TO_ID,
            'next_id': _id_sequence
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        return False

def load_from_file(filename: str = DEFAULT_DATA_FILE) -> bool:
    """
    JSON 파일에서 브랜드 데이터를 불러옵니다.

    Args:
        filename (str): 불러올 파일 이름

    Returns:
        bool: 성공 여부
    """
    global BRAND_NAME_TO_ID, BRAND_ID_TO_NAME, _id_sequence, _current_max_id

    if not os.path.exists(filename):
        print(f"파일을 찾을 수 없습니다: {filename}")
        return False

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 데이터 로드
        BRAND_NAME_TO_ID = data['brands']
        BRAND_ID_TO_NAME = {v: k for k, v in BRAND_NAME_TO_ID.items()}
        _id_sequence = data['next_id']
        _current_max_id = max(BRAND_ID_TO_NAME.keys()) if BRAND_ID_TO_NAME else 0

        print(f"브랜드 데이터를 '{filename}' 파일에서 불러왔습니다. (총 {len(BRAND_NAME_TO_ID)}개)")

        # SQL 파일 업데이트
        _update_sql_file()

        return True

    except Exception as e:
        print(f"파일 로드 중 오류 발생: {e}")
        return False

def search_brands(keyword: str) -> list:
    """
    키워드로 브랜드를 검색합니다.

    Args:
        keyword (str): 검색 키워드

    Returns:
        list: 검색된 브랜드 목록 [(name, id), ...]
    """
    keyword = keyword.lower()
    results = []

    for name, id_val in BRAND_NAME_TO_ID.items():
        if keyword in name.lower():
            results.append((name, id_val))

    return sorted(results, key=lambda x: x[1])  # ID순으로 정렬

def export_brands_to_txt(filename: str = "brands_export.txt") -> bool:
    """
    브랜드 목록을 텍스트 파일로 내보냅니다.

    Args:
        filename (str): 출력 파일 이름

    Returns:
        bool: 성공 여부
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"총 브랜드 수: {get_brand_count()}\n")
            f.write("=" * 50 + "\n")

            for name, id_val in get_all_brands():
                f.write(f"{id_val:4d}. {name}\n")

        print(f"브랜드 목록이 '{filename}' 파일로 저장되었습니다.")
        return True

    except Exception as e:
        print(f"파일 내보내기 중 오류 발생: {e}")
        return False

def generate_sql_file(transaction=None):
    """
    현재 브랜드 목록으로 SQL 파일을 생성합니다.

    Args:
        transaction: FileTransaction 객체 (트랜잭션 사용 시)
    """
    _update_sql_file(transaction)

# 모듈 로드 시 데이터 초기화
_initialize_data()

# 디버깅 및 테스트용
if __name__ == "__main__":
    # 현재 상태 출력
    print(f"현재 브랜드 수: {get_brand_count()}")
    print(f"현재 최대 ID: {_current_max_id}")
    print(f"다음 ID: {get_next_brand_id()}")

    # 테스트: 기존 브랜드 조회
    print("\n기존 브랜드 테스트:")
    test_brands = ['AHC', '닥터지', '달바']
    for brand in test_brands:
        brand_id = get_brand_id(brand)
        print(f"  '{brand}' -> ID: {brand_id}")

    # 테스트: 새로운 브랜드 자동 생성
    print("\n새로운 브랜드 테스트:")
    new_brand = '크롤링으로찾은새브랜드'
    new_brand_id = get_brand_id(new_brand)
    print(f"  '{new_brand}' -> ID: {new_brand_id}")

    # 테스트: 검색 기능
    print("\n브랜드 검색 테스트 (키워드: '닥터'):")
    search_results = search_brands('닥터')
    for name, id_val in search_results:
        print(f"  {name}: {id_val}")

    # 데이터 파일 정보
    print(f"\n데이터 파일: {DEFAULT_DATA_FILE}")
    print(f"SQL 파일: {SQL_OUTPUT_FILE}")

    # 상위 10개 브랜드 출력
    print(f"\n상위 10개 브랜드:")
    all_brands = get_all_brands()
    for i, (name, id_val) in enumerate(all_brands[:10], 1):
        print(f"  {i:2d}. {name} (ID: {id_val})")

    if len(all_brands) > 10:
        print(f"  ... 외 {len(all_brands) - 10}개")

    # 텍스트 파일로 내보내기
    export_brands_to_txt()