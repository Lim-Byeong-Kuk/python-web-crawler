import random
import os
from typing import List, Dict


def create_product_options_sql(product_id: int, product_options: List[Dict], transaction,
                               filename: str = "product_options_sql.txt") -> bool:
    """
    수집된 상품 옵션 정보를 product_options 테이블 INSERT문에 VALUES만 추가합니다.
    기존 INSERT문이 있으면 마지막 세미콜론을 쉼표로 변경하고 새 데이터를 추가합니다.

    Args:
        product_id: 상품 ID
        product_options: get_product_options()에서 반환된 옵션 리스트
        transaction: FileTransaction 객체
        filename: SQL 파일명

    Returns:
        bool: 성공 여부
    """

    if not product_options:
        print("⚠ 저장할 옵션 데이터가 없습니다.")
        return False

    try:
        # 기존 파일 내용 읽기
        file_content = ""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                file_content = f.read()

        # 새로운 VALUES 생성
        sql_values = []
        for idx, option in enumerate(product_options):
            option_name = option.get('name', '옵션명 없음').replace("'", "''")

            try:
                selling_price = int(option.get('price', '0'))
            except (ValueError, TypeError):
                selling_price = 0

            purchase_price = selling_price // 2
            current_stock = random.randint(50, 150)
            initial_stock = current_stock + random.randint(0, 50)
            safety_stock = 10
            image_url = option.get('image_url', '').replace("'", "''")
            display_order = idx
            is_deleted = 'true' if option.get('is_soldout', False) else 'false'

            sql_value = (
                f"({product_id}, '{option_name}', {purchase_price}, {selling_price}, "
                f"{current_stock}, {initial_stock}, {safety_stock}, "
                f"'{image_url}', {display_order}, "
                f"{is_deleted}, NOW(), NOW())"
            )
            sql_values.append(sql_value)

        # 기존 파일이 있고 INSERT문이 있는 경우
        if file_content and "INSERT INTO product_options" in file_content:
            # 마지막 세미콜론을 쉼표로 변경
            if file_content.rstrip().endswith(';'):
                file_content = file_content.rstrip()[:-1] + ','

            # 새 VALUES 추가
            new_content = file_content + "\n" + ",\n".join(sql_values) + ";\n\n"

            # 전체 파일 덮어쓰기
            transaction.write_file(filename, new_content)
        else:
            # 파일이 없거나 INSERT문이 없는 경우 - 새로 생성
            sql_text = ""
            sql_text += "INSERT INTO product_options\n"
            sql_text += "(product_id, option_name, purchase_price, selling_price,\n"
            sql_text += " current_stock, initial_stock, safety_stock,\n"
            sql_text += " image_url, display_order,\n"
            sql_text += " is_deleted, created_at, updated_at)\n"
            sql_text += "VALUES\n"
            sql_text += ",\n".join(sql_values)
            sql_text += ";\n\n"

            transaction.write_file(filename, sql_text)

        print(f"✓ Product ID {product_id}의 옵션 {len(product_options)}개가 '{filename}'에 추가되었습니다.")
        return True

    except Exception as e:
        print(f"✗ 옵션 SQL 생성 중 오류 발생: {e}")
        return False


def create_product_options_sql_with_validation(product_id: int, product_options: List[Dict], transaction,
                                               filename: str = "product_options_sql.txt") -> bool:
    """
    유효성 검증을 포함한 product_options SQL 생성 함수 (기존 INSERT문에 VALUES만 추가)

    Args:
        product_id: 상품 ID
        product_options: get_product_options()에서 반환된 옵션 리스트
        transaction: FileTransaction 객체
        filename: SQL 파일명

    Returns:
        bool: 성공 여부
    """

    if not product_options:
        print("⚠ 저장할 옵션 데이터가 없습니다.")
        return False

    # 유효한 옵션만 필터링
    valid_options = []
    for option in product_options:
        if (option.get('name') and
                option.get('name') != '옵션명 추출 실패' and
                option.get('price') and
                option.get('price') != '가격 추출 실패'):
            valid_options.append(option)
        else:
            print(f"⚠ 유효하지 않은 옵션 스킵: {option.get('name', 'N/A')}")

    if not valid_options:
        print("✗ 유효한 옵션이 없습니다.")
        return False

    try:
        # 기존 파일 내용 읽기
        file_content = ""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                file_content = f.read()

        # 새로운 VALUES 생성
        sql_values = []
        debug_lines = []

        for idx, option in enumerate(valid_options):
            option_name = option.get('name', '옵션명 없음').replace("'", "''")

            try:
                selling_price = int(option.get('price', '0'))
            except (ValueError, TypeError):
                selling_price = 0

            purchase_price = selling_price // 2

            if option.get('is_soldout', False):
                current_stock = 0
                initial_stock = random.randint(50, 100)
            else:
                current_stock = random.randint(50, 150)
                initial_stock = current_stock + random.randint(0, 50)

            safety_stock = 10
            image_url = option.get('image_url', '').replace("'", "''")
            display_order = idx
            is_deleted = 'true' if option.get('is_soldout', False) else 'false'

            sql_value = (
                f"({product_id}, '{option_name}', {purchase_price}, {selling_price}, "
                f"{current_stock}, {initial_stock}, {safety_stock}, "
                f"'{image_url}', {display_order}, "
                f"{is_deleted}, NOW(), NOW())"
            )

            sql_values.append(sql_value)
            debug_lines.append(f"  [{idx}] {option_name}: {selling_price}원, 재고: {current_stock}, 품절: {is_deleted}")

        # 기존 파일이 있고 INSERT문이 있는 경우
        if file_content and "INSERT INTO product_options" in file_content:
            # 마지막 세미콜론을 쉼표로 변경
            if file_content.rstrip().endswith(';'):
                file_content = file_content.rstrip()[:-1] + ','

            # 새 VALUES 추가
            new_content = file_content + "\n" + ",\n".join(sql_values) + ";\n\n"

            # 전체 파일 덮어쓰기
            transaction.write_file(filename, new_content)
        else:
            # 파일이 없거나 INSERT문이 없는 경우 - 새로 생성
            sql_text = ""
            sql_text += "INSERT INTO product_options\n"
            sql_text += "(product_id, option_name, purchase_price, selling_price,\n"
            sql_text += " current_stock, initial_stock, safety_stock,\n"
            sql_text += " image_url, display_order,\n"
            sql_text += " is_deleted, created_at, updated_at)\n"
            sql_text += "VALUES\n"
            sql_text += ",\n".join(sql_values)
            sql_text += ";\n\n"

            transaction.write_file(filename, sql_text)

        # 디버깅 출력
        for line in debug_lines:
            print(line)

        print(f"\n✓ Product ID {product_id}의 유효한 옵션 {len(valid_options)}개가 '{filename}'에 추가되었습니다.")
        return True

    except Exception as e:
        print(f"✗ 옵션 SQL 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False