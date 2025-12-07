import random
import os
from typing import List, Dict


def create_product_options_sql(product_id: int, product_options: List[Dict], transaction, # transaction 인자 추가
                               filename: str = "product_options_sql.txt") -> bool:
    """
    수집된 상품 옵션 정보를 product_options 테이블 INSERT문으로 변환하여 트랜잭션으로 파일에 저장합니다.

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
        # 파일에 추가할 SQL 텍스트 생성
        sql_text = ""
        sql_text += "\n-- ========================================\n"
        sql_text += f"-- Product ID: {product_id} 옵션 데이터\n"
        sql_text += "-- ========================================\n"
        sql_text += "INSERT INTO product_options\n"
        sql_text += "(product_id, option_name, purchase_price, selling_price,\n"
        sql_text += " current_stock, initial_stock, safety_stock,\n"
        sql_text += " image_url, display_order,\n"
        sql_text += " is_deleted, created_at, updated_at)\n"
        sql_text += "VALUES\n"

        sql_values = []

        for idx, option in enumerate(product_options):
            # 옵션명
            option_name = option.get('name', '옵션명 없음').replace("'", "''")  # SQL 이스케이프

            # 판매가격 (문자열로 된 숫자를 int로 변환)
            try:
                selling_price = int(option.get('price', '0'))
            except (ValueError, TypeError):
                selling_price = 0

            # 매입가격 (판매가의 절반)
            purchase_price = selling_price // 2

            # 재고 (임의 생성)
            current_stock = random.randint(50, 150)
            initial_stock = current_stock + random.randint(0, 50)
            safety_stock = 10

            # 이미지 URL
            image_url = option.get('image_url', '').replace("'", "''")  # SQL 이스케이프

            # display_order (0부터 시작)
            display_order = idx

            # 품절 여부
            is_deleted = 'true' if option.get('is_soldout', False) else 'false'

            # SQL VALUES 문 생성
            sql_value = (
                f"({product_id}, '{option_name}', {purchase_price}, {selling_price}, "
                f"{current_stock}, {initial_stock}, {safety_stock}, "
                f"'{image_url}', {display_order}, "
                f"{is_deleted}, NOW(), NOW())"
            )

            sql_values.append(sql_value)

        # SQL VALUES를 쉼표로 연결
        sql_text += ",\n".join(sql_values)
        sql_text += ";\n\n"

        # 트랜잭션으로 파일에 추가
        transaction.append_file(filename, sql_text)
        print(f"✓ Product ID {product_id}의 옵션 {len(product_options)}개가 '{filename}'에 트랜잭션으로 저장되었습니다.")
        return True

    except Exception as e:
        print(f"✗ 옵션 SQL 생성 중 오류 발생: {e}")
        return False


def create_product_options_sql_with_validation(product_id: int, product_options: List[Dict], transaction, # transaction 인자 추가
                                               filename: str = "product_options_sql.txt") -> bool:
    """
    유효성 검증을 포함한 product_options SQL 생성 함수 (트랜잭션 적용)

    Args:
        product_id: 상품 ID
        product_options: get_product_options()에서 반환된 옵션 리스트
        transaction: FileTransaction 객체 (추가)
        filename: SQL 파일명

    Returns:
        bool: 성공 여부
    """

    if not product_options:
        print("⚠ 저장할 옵션 데이터가 없습니다.")
        return False

    # 유효한 옵션만 필터링 (기존 로직 유지)
    valid_options = []
    for option in product_options:
        # 필수 필드 검증
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
        # 파일에 추가할 SQL 텍스트를 메모리에서 먼저 완성
        sql_text = ""
        sql_text += "INSERT INTO product_options\n"
        sql_text += "(product_id, option_name, purchase_price, selling_price,\n"
        sql_text += " current_stock, initial_stock, safety_stock,\n"
        sql_text += " image_url, display_order,\n"
        sql_text += " is_deleted, created_at, updated_at)\n"
        sql_text += "VALUES\n"

        sql_values = []
        debug_lines = []

        for idx, option in enumerate(valid_options):
            # 옵션명 (SQL 인젝션 방지)
            option_name = option.get('name', '옵션명 없음').replace("'", "''")

            # 판매가격
            try:
                selling_price = int(option.get('price', '0'))
            except (ValueError, TypeError):
                selling_price = 0

            # 매입가격 (판매가의 50%)
            purchase_price = selling_price // 2

            # 재고 설정 (품절 상품은 재고 0)
            if option.get('is_soldout', False):
                current_stock = 0
                initial_stock = random.randint(50, 100)
            else:
                current_stock = random.randint(50, 150)
                initial_stock = current_stock + random.randint(0, 50)

            safety_stock = 10

            # 이미지 URL
            image_url = option.get('image_url', '').replace("'", "''")

            # display_order
            display_order = idx

            # 품절 여부
            is_deleted = 'true' if option.get('is_soldout', False) else 'false'

            # SQL VALUES 문 생성
            sql_value = (
                f"({product_id}, '{option_name}', {purchase_price}, {selling_price}, "
                f"{current_stock}, {initial_stock}, {safety_stock}, "
                f"'{image_url}', {display_order}, "
                f"{is_deleted}, NOW(), NOW())"
            )

            sql_values.append(sql_value)

            # 디버깅 출력 내용을 저장
            debug_lines.append(f"  [{idx}] {option_name}: {selling_price}원, 재고: {current_stock}, 품절: {is_deleted}")


        # SQL VALUES를 쉼표로 연결
        sql_text += ",\n".join(sql_values)
        sql_text += ";\n\n"

        # 트랜잭션을 사용하여 파일에 추가 (기존 open('a') 로직 대체)
        transaction.append_file(filename, sql_text)

        # 디버깅 출력은 파일 작성 후 별도로 처리
        for line in debug_lines:
             print(line)

        print(f"\n✓ Product ID {product_id}의 유효한 옵션 {len(valid_options)}개가 '{filename}'에 트랜잭션으로 저장되었습니다.")
        return True

    except Exception as e:
        print(f"✗ 옵션 SQL 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False