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

    return uc.Chrome(options=options, version_main=143, use_subprocess=True)


def crawl_single_product(driver, product_url):
    """
    단일 상품 상세 페이지를 크롤링하는 함수

    Args:
        driver: 웹드라이버
        product_url: 상품 상세 페이지 URL

    Returns:
        bool: 크롤링 성공 여부
    """
    try:
        print(f"\n{'=' * 60}")
        print(f"상품 크롤링 시작")
        print(f"상품 URL: {product_url}")
        print(f"{'=' * 60}")

        # 상품 상세 페이지로 이동
        driver.get(product_url)
        time.sleep(5)  # 페이지 로딩 대기

        print(f"페이지 제목: {driver.title}")
        print(f"현재 URL: {driver.current_url}")

        # ========================================
        # 상세페이지에서 데이터 크롤링 (트랜잭션 적용)
        # ========================================
        crawl_success = False

        try:
            with FileTransaction() as transaction:
                # 상세 페이지 크롤링 함수 호출 (product_counter는 1로 고정)
                crawl_product_on_detail_page(driver, transaction, product_counter=1)
                # 예외가 없으면 자동으로 commit됨
                crawl_success = True
                print("\n✓ 상품 데이터 크롤링 및 저장 완료")

        except ValueError as ve:
            # 비즈니스 로직 예외 (중복 상품, 필수 데이터 누락 등)
            print(f"\n✗ 상품 검증 오류: {ve}")
            print("  → 데이터가 저장되지 않았습니다.")
            # 트랜잭션은 자동으로 rollback됨
            return False

        except Exception as detail_error:
            # 일반 예외 (네트워크 오류, 크롤링 실패 등)
            print(f"\n✗ 상품 크롤링 중 오류: {detail_error}")
            traceback.print_exc()

            # 상세 페이지 크롤링 오류 스크린샷 저장
            try:
                driver.save_screenshot("error_single_product.png")
                print(f"오류 스크린샷 저장: error_single_product.png")
            except:
                pass

            # 트랜잭션은 자동으로 rollback됨
            return False

        return crawl_success

    except Exception as e:
        print(f"\n✗ 상품 페이지 접근 중 오류: {e}")
        traceback.print_exc()

        # 오류 스크린샷 저장
        try:
            driver.save_screenshot("error_page_access.png")
            print(f"오류 스크린샷 저장: error_page_access.png")
        except:
            pass

        return False


def main():
    """메인 실행 함수"""
    driver = None

    try:
        # 드라이버 생성
        print("드라이버 생성 중...")
        driver = create_driver()
        print("✓ 드라이버 생성 완료")

        # 사용자로부터 상품 URL 입력받기
        print("\n" + "=" * 60)
        print("단일 상품 크롤러 (Single Product Crawler)")
        print("=" * 60)
        print("\n크롤링할 상품 상세 페이지 URL을 입력하세요:")
        print("예시: https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000123456")

        product_url = input("\nURL 입력: ").strip()

        # URL 검증
        if not product_url:
            print("\n✗ URL이 입력되지 않았습니다.")
            return

        if not product_url.startswith("http"):
            print("\n✗ 올바른 URL 형식이 아닙니다. (http:// 또는 https://로 시작해야 합니다)")
            return

        # 크롤링 실행
        print("\n크롤링을 시작합니다...")
        success = crawl_single_product(driver, product_url)

        # 결과 출력
        print("\n" + "=" * 60)
        if success:
            print("✓ 크롤링 성공!")
            print("  → 상품 데이터가 파일에 저장되었습니다.")
        else:
            print("✗ 크롤링 실패")
            print("  → 데이터가 저장되지 않았습니다.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 프로그램이 중단되었습니다.")

    except Exception as e:
        print(f"\n✗ 메인 실행 중 오류: {e}")
        traceback.print_exc()

    finally:
        # 드라이버 종료
        if driver:
            print("\n드라이버 종료 중...")

            try:
                # 최종 스크린샷 저장 (디버깅용)
                try:
                    driver.save_screenshot("final_screenshot.png")
                    print("최종 스크린샷 저장: final_screenshot.png")
                except:
                    pass

                # 모든 창 닫기
                for handle in driver.window_handles:
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                        time.sleep(0.1)
                    except:
                        pass

                # 드라이버 참조 제거
                driver_ref = driver
                del driver

                # garbage collection 강제 실행
                import gc
                gc.collect()

                print("✓ 드라이버 종료 완료")

            except Exception as e:
                print(f"✗ 드라이버 종료 중 오류 (무시): {e}")

            print("\n프로그램 종료")
            time.sleep(1)


if __name__ == "__main__":
    main()