import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
from file_transaction import FileTransaction
from crawl import crawl_product_on_detail_page


def create_driver():
    """드라이버 생성 함수"""
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")

    return uc.Chrome(options=options, version_main=137, use_subprocess=True)


def go_back_to_original_page(driver, original_url):
    """
    상세 페이지에서 원래 페이지로 돌아가는 함수
    - POST 요청 후 양식 재제출 문제 해결
    """
    print("\n뒤로가기 시도 중...")

    # 현재 URL 저장
    current_url_before = driver.current_url
    print(f"뒤로가기 전 URL: {current_url_before}")

    # 방법 1: GET 요청으로 직접 페이지 이동 (가장 확실)
    print("GET 요청으로 직접 페이지 이동")
    try:
        driver.get(original_url)
        time.sleep(3)  # 페이지 로딩 대기

        # 페이지가 완전히 로드될 때까지 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "Container"))
            )
            print("✓ GET 요청으로 페이지 이동 완료")
        except:
            print("페이지 로드 대기 중 타임아웃, 계속 진행")

    except Exception as e:
        print(f"GET 요청 이동 중 오류: {e}")
        # 방법 2: 뒤로가기 시도 (대체 방법)
        try:
            print("GET 요청 실패, 뒤로가기 시도")
            driver.execute_script("window.history.back();")
            time.sleep(3)

            # 경고창 처리 (양식 재제출 확인)
            try:
                alert = driver.switch_to.alert
                print(f"경고창 발견: {alert.text}")
                alert.accept()  # '계속' 버튼 클릭
                print("경고창 처리 완료")
                time.sleep(2)
            except:
                # 경고창 없음
                pass

        except Exception as back_error:
            print(f"뒤로가기도 실패: {back_error}")

    # 현재 URL 확인
    current_url_after = driver.current_url
    print(f"이동 후 URL: {current_url_after}")

    # 페이지 제목 확인
    try:
        print(f"이동 후 페이지 제목: {driver.title}")
    except:
        print("페이지 제목을 가져올 수 없음")

    # 페이지가 안정화될 때까지 추가 대기
    time.sleep(2)

    return True


def get_current_page_number(driver):
    """현재 페이지 번호를 가져오는 함수"""
    try:
        current_page_element = driver.find_element(By.XPATH, '//*[@id="Container"]/div[2]/strong[@title="현재 페이지"]')
        current_page = int(current_page_element.text.strip())
        return current_page
    except Exception as e:
        print(f"현재 페이지 번호를 가져오는 중 오류: {e}")
        return None


def click_next_page(driver, current_page):
    """
    다음 페이지로 이동하는 함수

    Args:
        driver: 웹드라이버
        current_page: 현재 페이지 번호

    Returns:
        bool: 성공 여부
    """
    try:
        print(f"\n현재 페이지: {current_page}, 다음 페이지로 이동 시도...")

        # 페이지네이션 컨테이너 찾기
        pagination_container = driver.find_element(By.XPATH, '//*[@id="Container"]/div[2]')

        # 다음 페이지 번호 계산
        next_page = current_page + 1

        # 1. 먼저 직접 페이지 번호 버튼 찾기 시도 (data-page-no 속성 사용)
        try:
            next_button = pagination_container.find_element(
                By.XPATH, f'.//a[@data-page-no="{next_page}"]'
            )
            print(f"✓ {next_page}페이지 버튼 찾음 (data-page-no)")
            next_button.click()
            time.sleep(3)
            return True
        except:
            print(f"{next_page}페이지 직접 버튼을 찾지 못함")

        # 2. "다음 10 페이지" 버튼 찾기 (10, 20, 30... 페이지로 넘어갈 때)
        try:
            next_10_button = pagination_container.find_element(
                By.XPATH, './/a[@class="next"]'
            )
            print(f"✓ '다음 10 페이지' 버튼 찾음")
            next_10_button.click()
            time.sleep(3)
            return True
        except:
            print("'다음 10 페이지' 버튼을 찾지 못함")

        # 3. 모든 a 태그를 순회하며 다음 페이지 찾기
        try:
            page_links = pagination_container.find_elements(By.TAG_NAME, 'a')
            for link in page_links:
                try:
                    page_no = link.get_attribute('data-page-no')
                    if page_no and int(page_no) == next_page:
                        print(f"✓ {next_page}페이지 버튼 찾음 (순회)")
                        link.click()
                        time.sleep(3)
                        return True
                except:
                    continue
        except:
            pass

        print(f"✗ 다음 페이지({next_page})로 이동할 수 없음")
        return False

    except Exception as e:
        print(f"다음 페이지 이동 중 오류: {e}")
        traceback.print_exc()
        return False


def has_next_page(driver, current_page):
    """
    다음 페이지가 있는지 확인하는 함수

    Args:
        driver: 웹드라이버
        current_page: 현재 페이지 번호

    Returns:
        bool: 다음 페이지 존재 여부
    """
    try:
        pagination_container = driver.find_element(By.XPATH, '//*[@id="Container"]/div[2]')
        next_page = current_page + 1

        # 1. 다음 페이지 번호 버튼이 있는지 확인
        try:
            pagination_container.find_element(By.XPATH, f'.//a[@data-page-no="{next_page}"]')
            return True
        except:
            pass

        # 2. "다음 10 페이지" 버튼이 있는지 확인
        try:
            pagination_container.find_element(By.XPATH, './/a[@class="next"]')
            return True
        except:
            pass

        return False

    except Exception as e:
        print(f"다음 페이지 확인 중 오류: {e}")
        return False


def crawl_products_on_current_page(driver, original_url, max_products=0):
    """
    현재 페이지의 모든 상품을 크롤링하는 함수

    Args:
        driver: 웹드라이버
        original_url: 현재 페이지 URL
        max_products: 최대 크롤링할 상품 수 (0이면 모두)

    Returns:
        int: 처리한 상품 수
    """
    product_counter = 0

    try:
        # 각 행을 순회 (ul[2]부터 ul[7]까지)
        for row_num in range(2, 8):  # 2부터 7까지 (6개 행)
            # 최대 상품 수에 도달했는지 확인
            if max_products > 0 and product_counter >= max_products:
                break

            ul_xpath = f'//*[@id="Contents"]/ul[{row_num}]'

            try:
                # 해당 행의 ul 요소 찾기
                row_element = driver.find_element(By.XPATH, ul_xpath)
                print(f"\n{'=' * 50}")
                print(f"행 {row_num - 1} 처리 중 (XPath: {ul_xpath})")
                print(f"{'=' * 50}")

                # 해당 행의 모든 상품 찾기 (각 li 요소)
                products = row_element.find_elements(By.XPATH, "./li")
                print(f"이 행에서 찾은 상품 수: {len(products)}")

                # 각 상품을 순회
                for product_idx in range(1, len(products) + 1):
                    # 최대 상품 수에 도달했는지 확인
                    if max_products > 0 and product_counter >= max_products:
                        print(f"최대 상품 수({max_products})에 도달하여 크롤링 중단")
                        break

                    try:
                        product_counter += 1

                        # 각 상품의 링크 XPath 생성
                        product_xpath = f'{ul_xpath}/li[{product_idx}]/div/a'
                        print(f"\n{'─' * 30}")
                        print(f"상품 {product_counter} 클릭 시도 (XPath: {product_xpath})")

                        # 상품 링크 찾기
                        product_link = driver.find_element(By.XPATH, product_xpath)

                        # 상품명 가져오기 (있을 경우)
                        try:
                            product_name = product_link.get_attribute("title") or product_link.get_attribute(
                                "textContent") or "상품명 없음"
                            print(f"상품명: {product_name}")
                        except:
                            product_name = f"상품_{product_counter}"
                            print(f"상품명: {product_name} (기본값)")

                        # 상품 클릭
                        product_link.click()
                        time.sleep(5)  # 상세 페이지 로딩 대기

                        # 상세 페이지 URL 저장
                        detail_url = driver.current_url
                        print(f"상세 페이지 URL: {detail_url}")

                        # ========================================
                        # 상세페이지에서 데이터 크롤링 (트랜잭션 적용)
                        # ========================================
                        # 트랜잭션을 사용하여 원자성 보장
                        crawl_success = False
                        try:
                            print("상품 순회 로직")
                            # with FileTransaction() as transaction:
                            #     # 상세 페이지 크롤링 함수 호출
                            #     crawl_product_on_detail_page(driver, transaction, product_counter)
                            #     # 예외가 없으면 자동으로 commit됨
                            #     crawl_success = True

                        except ValueError as ve:
                            # 비즈니스 로직 예외 (중복 상품, 필수 데이터 누락 등)
                            print(f"✗ 상품 {product_counter} 검증 오류: {ve}")
                            print("  → 이 상품은 건너뛰고 다음 상품으로 진행합니다.")
                            # 트랜잭션은 자동으로 rollback됨

                        except Exception as detail_error:
                            # 일반 예외 (네트워크 오류, 크롤링 실패 등)
                            print(f"✗ 상품 {product_counter} 크롤링 중 오류: {detail_error}")
                            traceback.print_exc()

                            # 상세 페이지 크롤링 오류 스크린샷 저장
                            try:
                                driver.save_screenshot(f"error_detail_page_{product_counter}.png")
                                print(f"상세 페이지 오류 스크린샷 저장: error_detail_page_{product_counter}.png")
                            except:
                                pass

                            # 트랜잭션은 자동으로 rollback됨

                        # 크롤링 결과 요약
                        if crawl_success:
                            print(f"✓ 상품 {product_counter} 처리 완료 및 커밋됨")
                        else:
                            print(f"✗ 상품 {product_counter} 처리 실패 및 롤백됨")

                        # 트랜잭션 블록 밖에서 뒤로가기 (성공/실패 여부와 관계없이)
                        try:
                            go_back_to_original_page(driver, original_url)
                        except Exception as back_error:
                            print(f"✗ 뒤로가기 중 오류 발생: {back_error}")
                            traceback.print_exc()

                            # 뒤로가기 실패 시 원본 URL로 직접 이동 재시도
                            try:
                                print("원본 페이지로 직접 이동 재시도...")
                                driver.get(original_url)
                                time.sleep(3)
                                print("✓ 원본 페이지로 복귀 성공")
                            except Exception as navigate_error:
                                print(f"✗ 원본 페이지 복귀 실패: {navigate_error}")
                                # 이 경우에도 계속 진행하도록 함
                                pass

                        # 상품 간 약간의 대기 시간 추가
                        time.sleep(2)

                    except Exception as e:
                        print(f"상품 {product_counter} 처리 중 오류: {e}")
                        traceback.print_exc()

                        # 오류 발생시 스크린샷 저장
                        try:
                            driver.save_screenshot(f"error_product_{product_counter}.png")
                            print(f"오류 스크린샷 저장: error_product_{product_counter}.png")
                        except:
                            pass

                        # 오류 발생해도 계속 진행
                        continue

            except Exception as e:
                print(f"행 {row_num} 처리 중 오류: {e}")
                traceback.print_exc()

                # 오류 발생시 스크린샷 저장
                try:
                    driver.save_screenshot(f"error_row_{row_num}.png")
                    print(f"행 오류 스크린샷 저장: error_row_{row_num}.png")
                except:
                    pass

                # 오류 발생해도 계속 진행
                continue

    except Exception as e:
        print(f"현재 페이지 크롤링 중 오류: {e}")
        traceback.print_exc()

    return product_counter


def crawl_all_products(driver, start_url, max_products=0):
    """
    모든 페이지의 상품을 크롤링하는 메인 함수

    Args:
        driver: 웹드라이버
        start_url: 시작 URL
        max_products: 최대 크롤링할 상품 수 (0이면 모두)
    """
    driver.get(start_url)
    time.sleep(10)  # Cloudflare 우회 대기

    print("페이지 제목:", driver.title)

    total_products_crawled = 0

    while True:
        # 현재 페이지 번호 확인
        current_page = get_current_page_number(driver)

        if current_page is None:
            print("현재 페이지 번호를 확인할 수 없습니다. 크롤링 중단.")
            break

        # 현재 페이지 URL 저장
        current_page_url = driver.current_url
        print(f"\n{'#' * 60}")
        print(f"페이지 {current_page} 처리 시작")
        print(f"현재 페이지 URL: {current_page_url}")
        print(f"{'#' * 60}")

        # 현재 페이지의 상품 크롤링
        remaining_products = max_products - total_products_crawled if max_products > 0 else 0
        products_crawled = crawl_products_on_current_page(
            driver, current_page_url, remaining_products
        )

        total_products_crawled += products_crawled

        print(f"\n페이지 {current_page} 완료: {products_crawled}개 상품 처리")
        print(f"누적 처리 상품 수: {total_products_crawled}")

        # 최대 상품 수에 도달했는지 확인
        if max_products > 0 and total_products_crawled >= max_products:
            print(f"\n✓ 최대 상품 수({max_products})에 도달하여 크롤링 완료!")
            break

        # 다음 페이지가 있는지 확인
        if not has_next_page(driver, current_page):
            print(f"\n✓ 더 이상 다음 페이지가 없습니다. 크롤링 완료!")
            break

        # 다음 페이지로 이동
        print(f"\n다음 페이지로 이동 시도...")
        success = click_next_page(driver, current_page)

        if not success:
            print(f"✗ 다음 페이지로 이동 실패. 크롤링 중단.")
            break

        # 페이지 로딩 대기
        time.sleep(3)

        # 페이지 이동 확인
        new_page = get_current_page_number(driver)
        if new_page and new_page > current_page:
            print(f"✓ 페이지 {new_page}로 이동 성공")
        else:
            print(f"✗ 페이지 이동 실패 또는 페이지 번호 확인 불가")
            # 재시도
            driver.refresh()
            time.sleep(3)
            new_page = get_current_page_number(driver)
            if not new_page or new_page <= current_page:
                print("재시도 실패. 크롤링 중단.")
                break

    print(f"\n{'=' * 60}")
    print(f"크롤링 완료!")
    final_page = get_current_page_number(driver)
    if final_page:
        print(f"마지막 처리 페이지: {final_page}")
    print(f"총 처리한 상품 수: {total_products_crawled}")
    print(f"{'=' * 60}")


def main():
    """메인 실행 함수"""
    driver = None

    try:
        # 드라이버 생성
        driver = create_driver()

        # 시작 URL
        url = "https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=1000001000100130001&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=24&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=0&aShowCnt=0&bShowCnt=0&cShowCnt=0&trackingCd=Cat1000001000100130001_Small&amplitudePageGubun=&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EA%B4%80&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EC%83%81%EC%84%B8_%EC%86%8C%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&midCategory=%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd=&t_1st_category_type=%EB%8C%80_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4&t_2nd_category_type=%EC%A4%91_%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88&t_3rd_category_type=%EC%86%8C_%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88"

        # 사용자 입력 받기
        print("크롤링할 상품 수를 입력하세요 (0: 모두, 숫자: 지정된 수만큼)")
        user_input = input("입력: ").strip()

        try:
            max_products = int(user_input)
            if max_products < 0:
                print("음수는 입력할 수 없습니다. 모두 크롤링합니다.")
                max_products = 0
        except ValueError:
            print("잘못된 입력입니다. 모두 크롤링합니다.")
            max_products = 0

        if max_products == 0:
            print("모든 상품을 크롤링합니다...")
        else:
            print(f"{max_products}개의 상품을 크롤링합니다...")

        # 크롤링 실행
        crawl_all_products(driver, url, max_products)

    except Exception as e:
        print(f"메인 실행 중 오류: {e}")
        traceback.print_exc()

    finally:
        # 드라이버 종료
        if driver:
            print("\n드라이버 종료 시도 중...")

            try:
                # 창 닫기 전에 스크린샷 찍기 (디버깅용)
                driver.save_screenshot("final_screenshot.png")
                print("최종 스크린샷 저장됨: final_screenshot.png")
            except:
                pass

            try:
                # 1. 먼저 모든 창 닫기
                for handle in driver.window_handles:
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                        time.sleep(0.1)
                    except:
                        pass

                # 2. 명시적으로 드라이버 참조 제거 (메모리 해제)
                driver_ref = driver
                del driver

                # 3. garbage collection 강제 실행
                import gc
                gc.collect()

                print("✓ 드라이버 종료 프로세스 완료")

            except Exception as e:
                print(f"✗ 드라이버 종료 중 오류 발생 (무시): {e}")

            print("프로그램 완전 종료")

            # 프로그램 종료 전 짧은 대기
            time.sleep(1)


if __name__ == "__main__":
    main()