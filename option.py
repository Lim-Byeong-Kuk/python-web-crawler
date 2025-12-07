from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from typing import List, Dict
import re


# ===============================================
# 보조 함수: URL 정제
# ===============================================

def clean_image_url(url: str) -> str:
    """
    이미지 URL에서 불필요한 쿼리 파라미터를 제거합니다.
    """
    if not url:
        return url

    # &QT, &SF, &sharpen 등의 파라미터 제거
    cleaned = re.sub(r'[?&](QT|SF|sharpen)=[^&]*', '', url)
    return cleaned


# ===============================================
# 복수 옵션 수집을 위한 상수 정의
# ===============================================

# 옵션 버튼 (드롭다운 열기)
OPTION_BUTTON_SELECTOR = "#main > div.page_product-details-wrapper___t38G > div > div.page_right-section__Plw5V > div > div.PurchaseBottom_purchase-bottom__C_GnK > div.PurchaseBottom_purchase-bottom-contents__ztB1w > div.OptionSelector_option-selector__6Z4Bu > div.option-wrapper > div > div > button"

# 옵션 리스트 전체 컨테이너 (ul)
OPTION_LIST_CONTAINER_SELECTOR = "ul.OptionSelector_option-list__9iV9W"

# 개별 옵션 아이템 (li) - 전체 리스트에서 반복 선택
OPTION_ITEM_SELECTOR = "li.OptionSelector_option-item__yMYbC"

# 각 옵션 아이템 내부의 세부 요소들 (상대 경로)
OPTION_IMG_RELATIVE = "img"
OPTION_NAME_RELATIVE = "span.OptionSelector_option-item-tit__8zEjW"
OPTION_PRICE_RELATIVE = "span.OptionSelector_option-item-price__QiVwN"

# ===============================================
# 단일 옵션(기본 상품 정보)을 위한 상수 정의
# ===============================================

# 상품명
MAIN_PRODUCT_NAME_SELECTOR = "#main > div.page_product-details-wrapper___t38G > div > div.page_right-section__Plw5V > div > div.GoodsDetailInfo_goods-info__NvhCW > div.GoodsDetailInfo_title-area__unu7g > h3"

# 상품 가격
MAIN_PRODUCT_PRICE_SELECTOR = "#main > div.page_product-details-wrapper___t38G > div > div.page_right-section__Plw5V > div > div.GoodsDetailInfo_goods-info__NvhCW > div.GoodsDetailInfo_price-area__RE0Gc.GoodsDetailInfo_margin-top__41aCw > div > div > span > span:nth-child(1)"

# 메인 이미지 썸네일
MAIN_THUMBNAIL_IMAGE_SELECTOR = "#main > div.page_product-details-wrapper___t38G > div > div.page_left-section__qXr0Q > div.GoodsDetailCarousel_visual-container__1kSZN > div > div > div.swiper-wrapper > div.swiper-slide.swiper-slide-active > div > img"


# ===============================================
# 메인 함수: 옵션 정보 수집
# ===============================================

def get_product_options(driver: WebDriver) -> List[Dict]:
    """
    상품 상세 페이지에서 모든 옵션의 이미지 URL, 옵션명, 옵션 가격을 수집합니다.
    옵션이 없을 경우 (단일 옵션 상품), 메인 상품 정보를 가져와 단일 옵션으로 구성합니다.
    """
    options_data = []
    option_button = None
    is_multi_option = False

    print("\n--- 옵션 정보 수집 시작 ---")

    # 1. 옵션 버튼 클릭 시도
    try:
        option_button = driver.find_element(By.CSS_SELECTOR, OPTION_BUTTON_SELECTOR)
        driver.execute_script("arguments[0].click();", option_button)
        print("✓ 옵션 드롭다운 버튼 클릭 성공 (복수 옵션 상품으로 판단).")

        # 드롭다운이 열릴 때까지 명시적 대기
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, OPTION_LIST_CONTAINER_SELECTOR))
        )
        time.sleep(1)
        is_multi_option = True

    except (NoSuchElementException, TimeoutException):
        print("⚠ 옵션 버튼이나 옵션 리스트를 찾을 수 없습니다. (단일 옵션 상품으로 판단)")
        is_multi_option = False
    except Exception as e:
        print(f"✗ 옵션 버튼 클릭 중 예상치 못한 에러 발생: {type(e).__name__}")
        is_multi_option = False

    # ----------------------------------------------------
    # 복수 옵션 상품 처리 (✨ 수정된 부분)
    # ----------------------------------------------------
    if is_multi_option:
        try:
            # 옵션 리스트 컨테이너 찾기
            option_list = driver.find_element(By.CSS_SELECTOR, OPTION_LIST_CONTAINER_SELECTOR)

            # 모든 옵션 아이템(li) 찾기
            option_items = option_list.find_elements(By.CSS_SELECTOR, OPTION_ITEM_SELECTOR)

            print(f"✓ 총 {len(option_items)}개의 옵션을 발견했습니다.")

            for idx, item in enumerate(option_items):
                option = {
                    'index': idx + 1,
                    'name': '옵션명 추출 실패',
                    'price': '가격 추출 실패',
                    'image_url': '이미지 요소 없음',
                    'is_soldout': False  # 품절 여부
                }

                try:
                    # 품절 여부 확인 (클래스에 'is-soldout' 포함 시)
                    item_classes = item.get_attribute('class')
                    if 'is-soldout' in item_classes:
                        option['is_soldout'] = True

                    # 옵션명 추출
                    try:
                        name_element = item.find_element(By.CSS_SELECTOR, OPTION_NAME_RELATIVE)
                        option['name'] = name_element.text.strip()
                    except NoSuchElementException:
                        pass

                    # 옵션 가격 추출
                    try:
                        price_element = item.find_element(By.CSS_SELECTOR, OPTION_PRICE_RELATIVE)
                        price_text = price_element.text.strip()
                        option['price'] = re.sub(r'[^\d]', '', price_text)
                    except NoSuchElementException:
                        pass

                    # 옵션 이미지 추출
                    try:
                        img_element = item.find_element(By.CSS_SELECTOR, OPTION_IMG_RELATIVE)
                        img_src = img_element.get_attribute('src') or img_element.get_attribute('data-src')

                        if img_src:
                            if img_src.startswith('//'):
                                img_src = 'https:' + img_src
                            if img_src.startswith('http'):
                                option['image_url'] = clean_image_url(img_src)
                    except NoSuchElementException:
                        pass

                except Exception as e:
                    print(f"⚠ 옵션 항목 {idx + 1} 세부 정보 추출 중 에러: {e}")

                options_data.append(option)

                # 출력 (품절 표시 포함)
                soldout_mark = " [품절]" if option['is_soldout'] else ""
                print(
                    f"[옵션 {idx + 1}]{soldout_mark} 이름: {option['name']}, 가격: {option['price']}원, 이미지: {option['image_url'][:50]}...")

        except Exception as e:
            print(f"✗ 복수 옵션 항목 처리 중 에러 발생: {e}")

    # ----------------------------------------------------
    # 단일 옵션 상품 처리
    # ----------------------------------------------------
    else:
        print("단일 옵션 상품의 기본 정보를 수집합니다.")
        single_option = {
            'index': 1,
            'name': '단일 상품명',
            'price': '0',
            'image_url': 'URL 추출 실패',
            'is_soldout': False
        }

        # 상품명 가져오기
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, MAIN_PRODUCT_NAME_SELECTOR)
            single_option['name'] = name_element.text.strip()
            print(f"  ✓ 상품명 추출 성공: {single_option['name']}")
        except NoSuchElementException:
            print(f"  ✗ 단일 상품명 추출 실패.")

        # 상품 가격 가져오기
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, MAIN_PRODUCT_PRICE_SELECTOR)
            price_text = price_element.text.strip()
            single_option['price'] = re.sub(r'[^\d]', '', price_text)
            print(f"  ✓ 가격 추출 성공: {single_option['price']}원")
        except NoSuchElementException:
            print(f"  ✗ 단일 상품 가격 추출 실패.")

        # 메인 이미지 썸네일 URL 가져오기
        try:
            img_element = driver.find_element(By.CSS_SELECTOR, MAIN_THUMBNAIL_IMAGE_SELECTOR)
            img_src = img_element.get_attribute('src') or img_element.get_attribute('data-src')

            if img_src:
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                if img_src.startswith('http'):
                    single_option['image_url'] = clean_image_url(img_src)
                    print(f"  ✓ 썸네일 URL 추출 성공: {single_option['image_url'][:50]}...")
                else:
                    print("  ✗ 썸네일 URL 최종 추출 실패 (src/data-src 없음).")
        except NoSuchElementException:
            print(f"  ✗ 썸네일 URL 최종 추출 실패 (요소 없음).")

        options_data.append(single_option)
        print(f"[단일 옵션 결과] 이름: {single_option['name']}, 가격: {single_option['price']}원")

    print("--- 옵션 정보 수집 완료 ---\n")

    # 옵션 드롭다운 닫기
    try:
        if is_multi_option and option_button and option_button.is_displayed():
            driver.execute_script("arguments[0].click();", option_button)
            time.sleep(0.5)
            print("✓ 옵션 드롭다운 닫기 성공.")
    except Exception:
        pass

    return options_data


# ===============================================
# 옵션 정보 저장 함수
# ===============================================

def save_product_options(options_data: List[Dict], filename: str = "product_options.txt"):
    """
    수집된 상품 옵션 정보를 텍스트 파일에 저장합니다.
    """
    if not options_data:
        print("⚠ 저장할 옵션 데이터가 없습니다.")
        return

    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 50 + "\n")
            f.write("상품 옵션 정보\n")
            f.write("=" * 50 + "\n")

            for option in options_data:
                soldout_mark = " (품절)" if option.get('is_soldout', False) else ""
                f.write(f"--- 옵션 #{option.get('index', 'N/A')}{soldout_mark} ---\n")
                f.write(f"옵션명: {option.get('name', 'N/A')}\n")
                f.write(f"가격: {option.get('price', 'N/A')}원\n")
                f.write(f"이미지 URL: {option.get('image_url', 'N/A')}\n")
                f.write("-" * 20 + "\n")

        print(f"✓ 상품 옵션 정보가 '{filename}'에 저장되었습니다.")
    except Exception as e:
        print(f"✗ 상품 옵션 정보 저장 중 오류 발생: {e}")