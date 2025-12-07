import json
import random
import os
from datetime import datetime, timedelta

# JSON 파일 경로
JSON_FILE_PATH = "product_data.json"
SQL_FILE_PATH = "product_data_sql.txt"

def create_product_id_with_transaction(product_name, transaction):
    """
    새로운 제품 ID를 생성하고 JSON 파일에 트랜잭션으로 기록합니다.

    Args:
        product_name (str): 제품명
        transaction: FileTransaction 객체

    Returns:
        int: 새로 생성된 제품 ID 또는 0(중복된 경우)
    """
    # JSON 데이터 로드
    data = load_product_data()

    # 이미 존재하는 제품명인지 확인
    if product_name in data["products"]:
        return 0

    # 새 ID 할당
    new_id = data["next_id"]
    data["products"][product_name] = new_id

    # next_id 증가
    data["next_id"] += 1

    # JSON 파일 저장 (트랜잭션 적용)
    transaction.write_json(JSON_FILE_PATH, data)

    return new_id

def load_product_data():
    """JSON 파일에서 제품 데이터를 로드합니다."""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 파일이 없을 경우 기본 구조 생성
        return {"products": {}, "next_id": 1}


def save_product_data(data):
    """JSON 파일에 제품 데이터를 저장합니다."""
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_product_id(product_name):
    """
    새로운 제품 ID를 생성하거나 이미 존재하는 제품명인 경우 0을 반환합니다.

    Args:
        product_name (str): 제품명

    Returns:
        int: 새로 생성된 제품 ID 또는 0(중복된 경우)
    """
    # JSON 데이터 로드
    data = load_product_data()

    # 이미 존재하는 제품명인지 확인
    if product_name in data["products"]:
        return 0

    # 새 ID 할당
    new_id = data["next_id"]
    data["products"][product_name] = new_id

    # next_id 증가
    data["next_id"] += 1

    # JSON 파일 저장
    save_product_data(data)

    return new_id


def generate_random_datetime():
    """
    2024-01-01 00:00:00부터 2026-01-01 00:00:00 사이의 랜덤한 datetime을 생성합니다.

    Returns:
        str: 'YYYY-MM-DD HH:MM:SS' 형식의 문자열
    """
    # 시작일과 종료일 설정
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    end_date = datetime(2026, 1, 1, 0, 0, 0)

    # 두 날짜 사이의 차이 계산 (초 단위)
    delta_seconds = int((end_date - start_date).total_seconds())

    # 랜덤한 초 추가
    random_seconds = random.randint(0, delta_seconds)
    random_datetime = start_date + timedelta(seconds=random_seconds)

    # 문자열 형식으로 반환
    return random_datetime.strftime('%Y-%m-%d %H:%M:%S')


def create_initial_product_data_sql():
    """
    초기 product_data_sql.txt 파일을 생성합니다.
    파일이 이미 존재하면 아무 작업도 하지 않습니다.
    """
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():  # 빈 파일인 경우
                initial_sql = """INSERT INTO products (id, product_detail_info_id, brand_id, category_id, \
                                                       delivery_policy_id, use_restock_noti, product_name, product_code, \
                                                       search_keywords, exposure_status, sale_status, description, \
                                                       is_cancelable, is_deleted, created_at, updated_at) \
                                 VALUES \
                              """
                with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f_write:
                    f_write.write(initial_sql)
    except FileNotFoundError:
        # 파일이 없을 경우 생성
        initial_sql = """INSERT INTO products (id, product_detail_info_id, brand_id, category_id, delivery_policy_id, \
                                               use_restooti, product_name, product_code, search_keywords, \
                                               exposure_status, sale_status, description, is_cancelable, is_deleted, \
                                               created_at, updated_at) \
                         VALUES \
                      """
        with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(initial_sql)


def update_product_data_sql(product_id, product_detail_info_id, brand_id, category_id, product_name):
    """
    product_data_sql.txt 파일에 INSERT 문을 추가합니다. (수정된 버전)

    Args:
        product_id (int): 제품 ID
        product_detail_info_id (int): 제품 상세 정보 ID
        brand_id (int): 브랜드 ID
        category_id (int): 카테고리 ID
        product_name (str): 제품명

    Returns:
        str: 생성된 INSERT 문
    """
    # 랜덤한 datetime 생성
    created_at = generate_random_datetime()

    # INSERT 문 생성 (괄호로 감싸진 값들)
    insert_statement = f"({product_id}, {product_detail_info_id}, {brand_id}, {category_id}, 2, FALSE, '{product_name}', 'NONE', '{product_name}', 'EXPOSURE', 'ON_SALE', '설명없음', true, false, '{created_at}', '{created_at}')"

    # SQL 파일 읽기
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        # 파일이 없을 경우 초기 내용 생성
        content = """INSERT INTO products (id, product_detail_info_id, brand_id, category_id, delivery_policy_id, \
                                           use_restock_noti, product_name, product_code, search_keywords, \
                                           exposure_status, sale_status, description, is_cancelable, is_deleted, \
                                           created_at, updated_at) \
                     VALUES"""

    # 내용 정리
    content = content.strip()

    # 마지막 문자 확인 및 처리
    if content.endswith(';'):
        # 세미콜론으로 끝나면 제거 (VALUES; 또는 데이터행); 모두 처리)
        content = content[:-1].rstrip()

    # VALUES로 끝나는지 확인 (첫 데이터 추가)
    if content.endswith('VALUES'):
        # 첫 데이터이므로 줄바꿈 후 추가하고 세미콜론으로 마무리
        new_content = content + f"\n{insert_statement};"
    else:
        # 기존 데이터가 있으므로 콤마 추가 후 새 데이터 추가
        new_content = content + f",\n{insert_statement};"

    # SQL 파일 저장
    with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return insert_statement




# 모듈 임포트 시 초기 SQL 파일 생성
create_initial_product_data_sql()


# 테스트 함수
def test_sql_update():
    """SQL 업데이트 기능 테스트"""

    # 기존 SQL 파일 내용 백업
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            original_content = f.read()
        print("기존 SQL 파일 내용:")
        print(original_content)
        print("\n" + "=" * 50 + "\n")
    except FileNotFoundError:
        original_content = ""
        print("기존 SQL 파일이 없습니다.\n")

    # 테스트 데이터 추가
    test_product_name = "테스트 제품 100"
    product_id = create_product_id(test_product_name)

    if product_id > 0:
        print(f"새 제품 생성: {test_product_name} (ID: {product_id})")

        # SQL 업데이트
        insert_stmt = update_product_data_sql(
            product_id=product_id,
            product_detail_info_id=product_id,
            brand_id=1,
            category_id=1,
            product_name=test_product_name
        )

        print(f"생성된 INSERT 문: {insert_stmt}")

        # 업데이트된 내용 확인
        try:
            with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            print("\n업데이트된 SQL 파일 내용:")
            print(updated_content)

            # 마지막 줄 확인
            lines = updated_content.strip().split('\n')
            last_line = lines[-1].strip()
            print(f"\n마지막 줄: {last_line}")
            print(f"마지막 줄이 );로 끝나는가? {last_line.endswith(');')}")

        except FileNotFoundError:
            print("SQL 파일을 찾을 수 없습니다.")

    # 중복 테스트
    duplicate_id = create_product_id(test_product_name)
    print(f"\n중복 제품 테스트: {duplicate_id} (0이면 성공)")


# 테스트 코드
if __name__ == "__main__":
    # 초기 SQL 파일 생성 확인
    create_initial_product_data_sql()

    # 테스트 실행
    test_sql_update()