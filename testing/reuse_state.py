from playwright.sync_api import sync_playwright
import time

# Đường dẫn để lưu file trạng thái
STATE_FILE = "data/state.json"

def login_and_save_state():
    with sync_playwright() as p:
        # Khởi tạo trình duyệt
        browser = p.chromium.launch(headless=False)  # headless=False để bạn có thể thấy trình duyệt
        context = browser.new_context()

        # Mở trang X.com
        page = context.new_page()
        page.goto("https://x.com/login")

        # Thực hiện đăng nhập (thay bằng thông tin của bạn)
        page.fill("input[name='text']", "your_username_or_email")
        page.click("button[type='submit']")  # Nhấn nút tiếp tục
        page.fill("input[name='password']", "your_password")
        page.click("button[type='submit']")  # Nhấn nút đăng nhập

        # Chờ cho đến khi đăng nhập thành công (kiểm tra URL hoặc một yếu tố trên trang)
        page.wait_for_url("https://x.com/home")

        # Lưu trạng thái đăng nhập vào file
        context.storage_state(path=STATE_FILE)

        # Đóng trình duyệt
        browser.close()

def reuse_saved_state():
    with sync_playwright() as p:
        # Khởi tạo trình duyệt với trạng thái đã lưu
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)

        # Mở trang X.com
        page = context.new_page()
        page.goto("https://x.com/home")

        # Kiểm tra xem đã đăng nhập hay chưa
        if page.url == "https://x.com/home":
            print("Đăng nhập thành công từ trạng thái đã lưu!")
        else:
            print("Không thể đăng nhập, có thể trạng thái đã hết hạn.")

        # Thực hiện các tác vụ khác trên trang...
        
        time.sleep(30)

        # Đóng trình duyệt
        browser.close()
