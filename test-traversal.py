import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import traceback

from mainImgCol import save_urls_to_file, get_main_image_urls
from productInfo import print_product_info, save_product_info, get_product_basic_info
from detailImg import get_detail_image_urls
from productDetailInfoProvided import get_product_info_provided

# undetected-chromedriver 설정 (기존 설정 유지)
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")

# User-Agent 설정 (기존 설정 유지)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")

# version_main을 지정하지 않으면 자동으로 맞는 버전을 다운로드합니다 (기존 설정 유지)
driver = uc.Chrome(options=options, version_main=142, use_subprocess=True)

try:
    url = "https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=1000001000100130001&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=24&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=0&aShowCnt=0&bShowCnt=0&cShowCnt=0&trackingCd=Cat1000001000100130001_Small&amplitudePageGubun=&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EA%B4%80&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EC%83%81%EC%84%B8_%EC%86%8C%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&midCategory=%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd=&t_1st_category_type=%EB%8C%80_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4&t_2nd_category_type=%EC%A4%91_%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88&t_3rd_category_type=%EC%86%8C_%EC%8A%A4%ED%82%A8%2F%ED%86%A0%EB%84%88"

    driver.get(url)
    time.sleep(10)  # Cloudflare 우회 대기

    print("페이지 제목:", driver.title)

    # 원래 URL 저장 (뒤로가기 실패시 사용)
    original_url = driver.current_url
    print(f"원래 URL: {original_url}")

    try:
        # 상품 상세 페이지 클릭
        element = driver.find_element(By.XPATH, "//*[@id='Contents']/ul[2]/li[3]")
        element.click()
        time.sleep(5)

        # 상세 페이지 URL 저장
        detail_url = driver.current_url
        print(f"상세 페이지 URL: {detail_url}")


        print("\n뒤로가기 시도 중...")

        # 더 확실한 뒤로가기 방법 사용
        current_url_before = driver.current_url
        print(f"뒤로가기 전 URL: {current_url_before}")

        # 방법 1: 먼저 스크롤을 최상단으로 이동
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # 방법 2: 뒤로가기 시도
        driver.back()
        time.sleep(3)

        # 방법 3: 페이지 새로고침 (화면 업데이트)
        driver.refresh()
        time.sleep(3)

        # 방법 4: 만약 제대로 안돌아왔다면 원래 URL로 직접 이동
        current_url_after = driver.current_url
        print(f"뒤로가기 후 URL: {current_url_after}")

        if original_url not in current_url_after:
            print("제대로 돌아오지 않음, 원래 URL로 직접 이동")
            driver.get(original_url)
            time.sleep(3)
            print(f"직접 이동 후 URL: {driver.current_url}")
        else:
            print("✓ 성공적으로 이전 페이지로 복귀")

        # 페이지가 로드되었는지 확인
        print(f"최종 페이지 제목: {driver.title}")

        # 화면 업데이트를 위해 추가 조치
        driver.execute_script("""
            // 페이지 강제 업데이트
            if (document.readyState === 'complete') {
                // 페이지 로드 완료 후 요소 찾기 시도
                var elements = document.querySelectorAll('[id^="Contents"]');
                console.log('찾은 요소 수:', elements.length);
            }
        """)
        time.sleep(2)

    except Exception as e:
        print(f"요소를 찾을 수 없음: {e}")
        driver.save_screenshot("error_screenshot.png")

except Exception as e:
    print(f"전체 실행 중 오류: {e}")
    traceback.print_exc()

finally:
    # 드라이버 종료 문제 해결 (에러 무시)
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