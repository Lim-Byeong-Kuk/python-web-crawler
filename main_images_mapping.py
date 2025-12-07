import os

# SQL 파일 경로
SQL_FILE_PATH = "product_main_images_sql.txt"


def create_initial_product_main_images_sql(transaction=None): # transaction 인자 추가
    """
    초기 product_main_images_sql.txt 파일을 생성하거나 초기화합니다.
    """
    initial_sql = "INSERT INTO product_main_images (product_id, image_type, display_order, image_url) VALUES"

    if transaction:
        # 트랜잭션이 있을 경우 파일을 읽고/쓰기
        try:
            # 파일을 읽어서 내용 확인 (백업을 위해)
            with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                transaction.write_file(SQL_FILE_PATH, initial_sql)
        except FileNotFoundError:
            # 파일이 없을 경우 생성
            transaction.write_file(SQL_FILE_PATH, initial_sql)
    else:
        # 트랜잭션이 없을 경우 기존 로직 유지 (단독 실행용)
        try:
            with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f_write:
                        f_write.write(initial_sql)
        except FileNotFoundError:
            with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(initial_sql)


def update_product_main_images_sql(product_id, main_image_urls, transaction): # transaction 인자 추가
    """
    product_main_images_sql.txt 파일에 제품 이미지 INSERT 문을 트랜잭션으로 추가합니다.

    Args:
        product_id (int): 제품 ID
        main_image_urls (list): 이미지 URL 배열
        transaction (FileTransaction): 트랜잭션 객체
    """
    if not main_image_urls or len(main_image_urls) == 0:
        return []

    # SQL 파일 내용 읽기 (트랜잭션에 의해 백업됨)
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "INSERT INTO product_main_images (product_id, image_type, display_order, image_url) VALUES"

    # 내용 정리
    content = content.strip()

    # 마지막 세미콜론 제거
    if content.endswith(';'):
        content = content[:-1].rstrip()

    # INSERT 문 생성
    insert_statements = []

    for idx, image_url in enumerate(main_image_urls):
        display_order = idx
        image_type = 'THUMBNAIL' if display_order == 0 else 'GALLERY'

        # SQL 이스케이프
        escaped_image_url = image_url.replace("'", "''")

        insert_statement = f"({product_id}, '{image_type}', {display_order}, '{escaped_image_url}')"
        insert_statements.append(insert_statement)

    # VALUES로 끝나는지 확인 (첫 데이터 추가)
    if content.endswith('VALUES'):
        new_content = content
        for i, stmt in enumerate(insert_statements):
            if i == 0:
                new_content += f"\n{stmt}"
            else:
                new_content += f",\n{stmt}"
        new_content += ";"
    else:
        # 기존 데이터가 있으므로 콤마 추가 후 새 데이터 추가
        new_content = content
        for stmt in insert_statements:
            new_content += f",\n{stmt}"
        new_content += ";"

    # 트랜잭션을 사용하여 SQL 파일 저장
    transaction.write_file(SQL_FILE_PATH, new_content)

    return insert_statements


# 모듈 임포트 시 초기 SQL 파일 생성 (트랜잭션 없이)
create_initial_product_main_images_sql()