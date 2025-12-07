"""
상품 상세 페이지 크롤링 모듈
트랜잭션을 적용하여 원자성을 보장합니다.
"""

from file_transaction import FileTransaction
from brand_mapping import get_brand_id
from category_mapping import get_category_id
from mainImgCol import get_main_image_urls
from main_images_mapping import update_product_main_images_sql
from productInfo import print_product_info, get_product_basic_info
from detailImg import get_detail_image_urls
from product_mapping import create_product_id, update_product_data_sql, create_product_id_with_transaction
from productDetailInfoProvided import get_product_dtailinfo_provided, reset_product_detail_info_id
from option import get_product_options, save_product_options # 민석 추가, 저장 함수 추가
from product_options_mapping import create_product_options_sql, create_product_options_sql_with_validation


def crawl_product_on_detail_page(driver, transaction, product_counter):
    """
    상품 상세 페이지에서 데이터를 크롤링하고 파일을 업데이트합니다.
    모든 작업은 트랜잭션 내에서 수행되며, 예외 발생 시 자동으로 롤백됩니다.

    Args:
        driver: Selenium WebDriver 객체
        transaction: FileTransaction 객체
        product_counter: 현재 상품 번호 (로깅용)

    Raises:
        ValueError: 필수 데이터가 없거나 유효하지 않은 경우
        Exception: 크롤링 중 발생하는 모든 예외
    """

    print(f"\n{'=' * 60}")
    print(f"상품 {product_counter} 데이터 수집 시작")
    print(f"{'=' * 60}")

    # ============================================================
    # 1단계: 상품 기본 정보 수집 (병국)
    # ============================================================
    print("\n[1단계] 상품 기본 정보 수집 중...")
    category, brand, product_name = get_product_basic_info(driver)

    print(f"  - 카테고리: {category}")
    print(f"  - 브랜드: {brand}")
    print(f"  - 상품명: {product_name}")

    # ============================================================
    # 2단계: 상품 메인 이미지 수집
    # ============================================================
    print("\n[2단계] 메인 이미지 수집 중...")
    main_image_urls = get_main_image_urls(driver, 3)

    # 예외 처리: 메인 이미지가 없는 경우
    if not main_image_urls:
        raise ValueError(f"Error: 상품 {product_counter} - 메인 이미지 URL 배열이 비어있습니다.")

    print(f"  ✓ {len(main_image_urls)}개의 메인 이미지 수집 완료")

    # ============================================================
    # 3단계: Brand ID 및 Category ID 확인
    # ============================================================
    print("\n[3단계] Brand ID 및 Category ID 확인 중...")

    # brand_id 찾기 및 브랜드 SQL 파일 업데이트 (트랜잭션 적용)
    brand_id = get_brand_id(brand, transaction)
    print(f"  - Brand ID: {brand_id}")

    # category_id 찾기
    category_id = get_category_id(category)
    print(f"  - Category ID: {category_id}")

    # 예외 처리: category_id가 0인 경우
    if category_id == 0:
        raise ValueError(f"Error: 상품 {product_counter} - 유효한 카테고리 ID를 찾지 못했습니다. (category: {category})")

    # ============================================================
    # 4단계: Product ID 생성
    # ============================================================
    print("\n[4단계] Product ID 생성 중...")
    product_id = create_product_id_with_transaction(product_name, transaction)
    print(f"  - Product ID: {product_id}")

    # 예외 처리: product_id가 0인 경우 (이미 존재하는 상품)
    if product_id == 0:
        raise ValueError(f"Error: 상품 {product_counter} - 이미 존재하는 제품명입니다. (product_name: {product_name})")

    # ============================================================
    # 5단계: 상품 정보 제공 고시 수집 (소라)
    # ============================================================
    print("\n[5단계] 상품 정보 제공 고시 수집 중...")
    product_detail_info, product_detail_info_id = get_product_dtailinfo_provided(
        driver,
        transaction,
        filename="product_detailinfo_provided_sql.txt"
    )
    print(f"  ✓ 상품 정보 제공 고시 수집 완료 (ID: {product_detail_info_id})")

    # ============================================================
    # 6단계: 상품 상세 이미지 수집 (소라)
    # ============================================================
    print("\n[6단계] 상품 상세 이미지 수집 중...")

    detail_image_urls = get_detail_image_urls(
        driver,
        product_id,
        transaction,
        filename="detail_image_urls_sql.txt"
    )

    # 예외 처리: 상세 이미지가 없는 경우
    if not detail_image_urls:
        raise ValueError(f"Error: 상품 {product_counter} - 상세 이미지 URL 배열이 비어있습니다.")

    print(f"  ✓ {len(detail_image_urls)}개의 상세 이미지 수집 완료")

    # ============================================================
    # 7단계: 상품 데이터 SQL 업데이트
    # ============================================================
    print("\n[7단계] 상품 데이터 SQL 업데이트 중...")

    # 현재 SQL 파일 읽기
    try:
        with open("product_data_sql.txt", "r", encoding="utf-8") as f:
            current_sql = f.read()
    except FileNotFoundError:
        current_sql = "INSERT INTO products (id, product_detail_info_id, brand_id, category_id, delivery_policy_id, use_restock_noti, product_name, product_code, search_keywords, exposure_status, sale_status, description, is_cancelable, is_deleted, created_at, updated_at) VALUES"

    # SQL 생성
    from product_mapping import generate_random_datetime
    created_at = generate_random_datetime()

    insert_statement = f"({product_id}, {product_detail_info_id}, {brand_id}, {category_id}, 2, FALSE, '{product_name}', 'NONE', '{product_name}', 'EXPOSURE', 'ON_SALE', '설명없음', true, false, '{created_at}', '{created_at}')"

    # SQL 업데이트 (트랜잭션 적용)
    current_sql = current_sql.strip()
    if current_sql.endswith(';'):
        current_sql = current_sql[:-1].rstrip()

    if current_sql.endswith('VALUES'):
        new_sql = current_sql + f"\n{insert_statement};"
    else:
        new_sql = current_sql + f",\n{insert_statement};"

    transaction.write_file("product_data_sql.txt", new_sql)
    print(f"  ✓ 상품 데이터 SQL 업데이트 완료 (ID: {product_id})")

    # ============================================================
    # 8단계: 메인 이미지 SQL 업데이트
    # ============================================================
    print("\n[8단계] 메인 이미지 SQL 업데이트 중...")
    update_product_main_images_sql(product_id, main_image_urls, transaction)
    print(f"  ✓ 메인 이미지 SQL 업데이트 완료")

    # ============================================================
    # 9단계: 상품 옵션 정보 수집 (민석)
    # ============================================================
    print("\n[9단계] 상품 옵션 정보 수집 중...")
    product_options = get_product_options(driver)

    # 예외 처리: 옵션이 없는 경우
    if not product_options:
        raise ValueError(f"Error: 상품 {product_counter} - 상품 옵션 배열이 비어있습니다.")

    print(f"  ✓ {len(product_options)}개의 옵션 수집 완료")

    # ============================================================
    # 10단계: 옵션 SQL 생성 및 저장
    # ============================================================
    print("\n[10단계] 옵션 SQL 생성 중...")
    create_product_options_sql_with_validation(
        product_id=product_id,
        product_options=product_options,
        transaction=transaction,
        filename="product_options_sql.txt"
    )
    print(f"  ✓ 옵션 SQL 생성 완료")

    # ============================================================
    # 완료
    # ============================================================
    print(f"\n{'=' * 60}")
    print(f"상품 {product_counter} 데이터 수집 완료!")
    print(f"  - Product ID: {product_id}")
    print(f"  - 상품명: {product_name}")
    print(f"  - 메인 이미지: {len(main_image_urls)}개")
    print(f"  - 상세 이미지: {len(detail_image_urls)}개")
    print(f"  - 옵션: {len(product_options)}개")
    print(f"{'=' * 60}\n")


