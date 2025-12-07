from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re

FIELD_MAP = {
    "내용물의 용량 또는 중량": "capacity",
    "제품 주요 사양": "skin_type",
    "사용기한(또는 개봉 후 사용기간)": "usage_period",
    "사용방법": "usage_method",
    "화장품제조업자,화장품책임판매업자 및 맞춤형화장품판매업자": "manufacturer",
    "제조국": "made_in_country",
    "화장품법에 따라 기재해야 하는 모든 성분": "ingredients",
    "기능성 화장품 식품의약품안전처 심사필 여부": "functional_certification",
    "사용할 때의 주의사항": "caution",
    "품질보증기준": "quality_guarantee",
    "소비자상담 전화번호": "customer_service_number",
}

# 전역 변수로 ID 카운터 관리
_product_detail_info_id_counter = 0
_is_initialized = False
_last_filename = None


def escape_sql(value) -> str:
    """SQL에서 작은 따옴표 문제 방지"""
    if value is None:
        return ""
    return str(value).replace("'", "''")


def get_last_id_from_file(filename: str) -> int:
    """SQL 파일에서 마지막 ID를 읽어옵니다"""
    if not os.path.exists(filename):
        return 0

    try:
        with open(filename, "r", encoding='utf-8') as f:
            content = f.read()

        matches = re.findall(r'VALUES\s*\((\d+),', content)

        if matches:
            return max(int(id) for id in matches)

        return 0
    except:
        return 0


def auto_init_if_needed(filename: str = None):
    """필요시 자동으로 초기화"""
    global _product_detail_info_id_counter, _is_initialized, _last_filename

    if _is_initialized and _last_filename == filename:
        return

    if filename and os.path.exists(filename):
        last_id = get_last_id_from_file(filename)
        _product_detail_info_id_counter = last_id
    else:
        _product_detail_info_id_counter = 0

    _is_initialized = True
    _last_filename = filename


def init_product_detail_info_id(filename: str = None):
    """ID 카운터 초기화"""
    global _product_detail_info_id_counter, _is_initialized, _last_filename

    if filename and os.path.exists(filename):
        last_id = get_last_id_from_file(filename)
        _product_detail_info_id_counter = last_id
    else:
        _product_detail_info_id_counter = 0

    _is_initialized = True
    _last_filename = filename


def reset_product_detail_info_id():
    """ID 카운터를 0으로 완전히 초기화"""
    global _product_detail_info_id_counter, _is_initialized, _last_filename
    _product_detail_info_id_counter = 0
    _is_initialized = False
    _last_filename = None


def get_product_dtailinfo_provided(driver, filename: str = None):
    """
    상품정보 제공고시 테이블을 가져오는 함수
    ID는 자동으로 증가합니다.
    """
    global _product_detail_info_id_counter

    auto_init_if_needed(filename)

    try:
        _product_detail_info_id_counter += 1
        current_id = _product_detail_info_id_counter

        wait = WebDriverWait(driver, 10)

        button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="tab-panels"]/section/ul/li[1]/button/span')
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(1)

        table = driver.find_element(By.CSS_SELECTOR, "div.Accordion_content__aIya4 table.Accordion_table__mcFPq")

        rows = table.find_elements(By.TAG_NAME, "tr")
        product_info = {}

        for row in rows:
            try:
                key = row.find_element(By.TAG_NAME, "th").text.strip()
                value = row.find_element(By.TAG_NAME, "td").text.strip()
                product_info[key] = value
            except:
                continue

        print(f"상품정보 제공고시 {len(product_info)}개 항목 수집 완료")

        ordered_values = []
        for key, column in FIELD_MAP.items():
            value = product_info.get(key, "")
            ordered_values.append(f"'{escape_sql(str(value))}'")

        columns = ', '.join(FIELD_MAP.values())
        values = ', '.join(ordered_values)

        sql = f"INSERT INTO product_detail_info (id, {columns}, created_at, updated_at)\nVALUES ({current_id}, {values}, NOW(), NOW());\n\n"

        if filename:
            with open(filename, "a", encoding='utf-8') as f:
                f.write(sql)

        return product_info, current_id

    except Exception as e:
        print("상품정보 제공고시 수집 실패:", e)
        return None, _product_detail_info_id_counter