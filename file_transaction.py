import os
import shutil
import json
import traceback
from datetime import datetime


class FileTransaction:
    """
    파일 기반 트랜잭션 관리 클래스
    여러 파일 작업을 하나의 트랜잭션으로 묶어서 원자성을 보장합니다.
    """

    def __init__(self, backup_dir=".transaction_backup"):
        """
        Args:
            backup_dir: 백업 파일을 저장할 디렉토리
        """
        self.backup_dir = backup_dir
        self.backup_files = {}  # {원본_파일_경로: 백업_파일_경로}
        self.new_files = []  # 트랜잭션 중 새로 생성된 파일 목록
        self.is_active = False
        self.transaction_id = None

    def begin(self):
        """트랜잭션 시작"""
        if self.is_active:
            raise Exception("트랜잭션이 이미 시작되었습니다.")

        self.transaction_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.backup_files = {}
        self.new_files = []
        self.is_active = True

        # 백업 디렉토리 생성
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        print(f"[Transaction] 트랜잭션 시작 (ID: {self.transaction_id})")

    def backup_file(self, file_path):
        """
        파일을 백업합니다.

        Args:
            file_path: 백업할 파일 경로
        """
        if not self.is_active:
            raise Exception("트랜잭션이 시작되지 않았습니다.")

        # 이미 백업된 파일은 다시 백업하지 않음
        if file_path in self.backup_files:
            return

        # 파일이 존재하는 경우에만 백업
        if os.path.exists(file_path):
            backup_path = os.path.join(
                self.backup_dir,
                f"{self.transaction_id}_{os.path.basename(file_path)}.backup"
            )
            shutil.copy2(file_path, backup_path)
            self.backup_files[file_path] = backup_path
            print(f"[Transaction] 파일 백업: {file_path} -> {backup_path}")
        else:
            # 파일이 존재하지 않으면 새로 생성될 파일로 간주
            self.new_files.append(file_path)
            print(f"[Transaction] 새 파일로 등록: {file_path}")

    def write_file(self, file_path, content, mode='w', encoding='utf-8'):
        """
        트랜잭션 내에서 파일을 작성합니다.

        Args:
            file_path: 파일 경로
            content: 파일 내용
            mode: 쓰기 모드 ('w', 'a', 'wb' 등)
            encoding: 인코딩 (바이너리 모드가 아닐 때만)
        """
        if not self.is_active:
            raise Exception("트랜잭션이 시작되지 않았습니다.")

        # 파일 백업
        self.backup_file(file_path)

        # 파일 쓰기
        if 'b' in mode:
            with open(file_path, mode) as f:
                f.write(content)
        else:
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)

        print(f"[Transaction] 파일 작성: {file_path}")

    def write_json(self, file_path, data, indent=2, encoding='utf-8'):
        """
        트랜잭션 내에서 JSON 파일을 작성합니다.

        Args:
            file_path: JSON 파일 경로
            data: JSON으로 저장할 데이터
            indent: 들여쓰기
            encoding: 인코딩
        """
        if not self.is_active:
            raise Exception("트랜잭션이 시작되지 않았습니다.")

        # 파일 백업
        self.backup_file(file_path)

        # JSON 파일 쓰기
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

        print(f"[Transaction] JSON 파일 작성: {file_path}")

    def append_file(self, file_path, content, encoding='utf-8'):
        """
        트랜잭션 내에서 파일에 내용을 추가합니다.

        Args:
            file_path: 파일 경로
            content: 추가할 내용
            encoding: 인코딩
        """
        self.write_file(file_path, content, mode='a', encoding=encoding)

    def commit(self):
        """트랜잭션 커밋 (백업 파일 삭제)"""
        if not self.is_active:
            raise Exception("트랜잭션이 시작되지 않았습니다.")

        # 백업 파일 삭제
        for backup_path in self.backup_files.values():
            if os.path.exists(backup_path):
                os.remove(backup_path)
                print(f"[Transaction] 백업 파일 삭제: {backup_path}")

        print(f"[Transaction] 트랜잭션 커밋 완료 (ID: {self.transaction_id})")

        # 상태 초기화
        self.backup_files = {}
        self.new_files = []
        self.is_active = False
        self.transaction_id = None

    def rollback(self):
        """트랜잭션 롤백 (원본 파일 복원)"""
        if not self.is_active:
            print("[Transaction] 트랜잭션이 활성화되지 않음, 롤백 불필요")
            return

        print(f"[Transaction] 트랜잭션 롤백 시작 (ID: {self.transaction_id})")

        # 백업 파일에서 원본 파일 복원
        for original_path, backup_path in self.backup_files.items():
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)
                print(f"[Transaction] 파일 복원: {backup_path} -> {original_path}")
                os.remove(backup_path)

        # 새로 생성된 파일 삭제
        for new_file in self.new_files:
            if os.path.exists(new_file):
                os.remove(new_file)
                print(f"[Transaction] 새 파일 삭제: {new_file}")

        print(f"[Transaction] 트랜잭션 롤백 완료 (ID: {self.transaction_id})")

        # 상태 초기화
        self.backup_files = {}
        self.new_files = []
        self.is_active = False
        self.transaction_id = None

    def __enter__(self):
        """Context manager 진입"""
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        if exc_type is not None:
            # 예외 발생 시 롤백
            print(f"[Transaction] 예외 발생: {exc_type.__name__}: {exc_val}")
            self.rollback()
            return False  # 예외를 다시 발생시킴
        else:
            # 정상 종료 시 커밋
            self.commit()
            return True


# 사용 예제 함수
def example_usage():
    """FileTransaction 사용 예제"""

    # 예제 1: 정상적인 트랜잭션 (커밋)
    print("\n" + "=" * 60)
    print("예제 1: 정상적인 트랜잭션")
    print("=" * 60)

    try:
        with FileTransaction() as transaction:
            # 파일 작성
            transaction.write_file("test1.txt", "첫 번째 파일 내용\n")
            transaction.write_file("test2.txt", "두 번째 파일 내용\n")

            # JSON 작성
            transaction.write_json("test_data.json", {
                "name": "테스트 제품",
                "price": 10000,
                "images": ["image1.jpg", "image2.jpg"]
            })

            print("모든 파일 작성 완료 -> 커밋됨")
    except Exception as e:
        print(f"예외 발생: {e}")

    # 예제 2: 예외 발생 시 롤백
    print("\n" + "=" * 60)
    print("예제 2: 예외 발생 시 롤백")
    print("=" * 60)

    # 먼저 초기 파일 생성
    with open("test_rollback.txt", "w") as f:
        f.write("초기 내용\n")

    print(f"초기 파일 내용: {open('test_rollback.txt').read()}")

    try:
        with FileTransaction() as transaction:
            # 파일 수정
            transaction.write_file("test_rollback.txt", "변경된 내용\n")

            # 새 파일 생성
            transaction.write_file("test_new.txt", "새로운 파일\n")

            # 의도적으로 예외 발생
            raise Exception("의도적인 예외 발생!")

    except Exception as e:
        print(f"예외 발생: {e}")

    # 롤백 후 파일 내용 확인
    print(f"롤백 후 파일 내용: {open('test_rollback.txt').read()}")
    print(f"새 파일 존재 여부: {os.path.exists('test_new.txt')}")


def example_with_product_crawling():
    """상품 크롤링 시뮬레이션 예제"""
    print("\n" + "=" * 60)
    print("예제 3: 상품 크롤링 트랜잭션")
    print("=" * 60)

    # 제품 데이터 파일들이 이미 있다고 가정
    product_data_sql_file = "product_data_sql.txt"
    product_images_sql_file = "product_main_images_sql.txt"
    product_json_file = "product_data.json"

    # 초기 데이터 생성
    with open(product_data_sql_file, "w") as f:
        f.write("INSERT INTO products VALUES\n(1, 'Product 1');\n")

    with open(product_images_sql_file, "w") as f:
        f.write("INSERT INTO images VALUES\n(1, 'image1.jpg');\n")

    with open(product_json_file, "w") as f:
        json.dump({"products": {"Product 1": 1}, "next_id": 2}, f)

    print("초기 데이터 생성 완료")

    # 성공 케이스
    print("\n--- 성공 케이스 ---")
    try:
        with FileTransaction() as transaction:
            # 제품 SQL 업데이트
            current_sql = open(product_data_sql_file).read()
            new_sql = current_sql.rstrip(';\n') + ",\n(2, 'Product 2');\n"
            transaction.write_file(product_data_sql_file, new_sql)

            # 이미지 SQL 업데이트
            current_images = open(product_images_sql_file).read()
            new_images = current_images.rstrip(';\n') + ",\n(2, 'image2.jpg');\n"
            transaction.write_file(product_images_sql_file, new_images)

            # JSON 업데이트
            json_data = json.load(open(product_json_file))
            json_data["products"]["Product 2"] = 2
            json_data["next_id"] = 3
            transaction.write_json(product_json_file, json_data)

            print("✓ 제품 2 추가 성공")
    except Exception as e:
        print(f"✗ 오류: {e}")

    # 실패 케이스 (롤백)
    print("\n--- 실패 케이스 (롤백) ---")
    try:
        with FileTransaction() as transaction:
            # 제품 SQL 업데이트
            current_sql = open(product_data_sql_file).read()
            new_sql = current_sql.rstrip(';\n') + ",\n(3, 'Product 3');\n"
            transaction.write_file(product_data_sql_file, new_sql)

            # 이미지 SQL 업데이트
            current_images = open(product_images_sql_file).read()
            new_images = current_images.rstrip(';\n') + ",\n(3, 'image3.jpg');\n"
            transaction.write_file(product_images_sql_file, new_images)

            # 중간에 예외 발생 (JSON 업데이트 전)
            raise Exception("네트워크 오류 발생!")

            # 이 코드는 실행되지 않음
            json_data = json.load(open(product_json_file))
            json_data["products"]["Product 3"] = 3
            json_data["next_id"] = 4
            transaction.write_json(product_json_file, json_data)

    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        print("✓ 롤백으로 인해 모든 변경사항이 취소됨")

    # 최종 상태 확인
    print("\n--- 최종 파일 상태 ---")
    print(f"SQL 파일:\n{open(product_data_sql_file).read()}")
    print(f"\n이미지 SQL 파일:\n{open(product_images_sql_file).read()}")
    print(f"\nJSON 파일:\n{open(product_json_file).read()}")


if __name__ == "__main__":
    # 기본 예제 실행
    example_usage()

    # 상품 크롤링 시뮬레이션 실행
    example_with_product_crawling()