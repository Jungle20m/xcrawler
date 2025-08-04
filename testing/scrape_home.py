from playwright.sync_api import sync_playwright
import time


def run():
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        # we can extract details from background requests
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response
    
    def wait_for_user_tweets(page, timeout=30000):
        """Wait until a UserTweets request has a response"""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            for xhr in _xhr_calls:
                print(xhr.url)
                if "HomeTimeline" in xhr.url: # check if the "UserTweets" is being called?
                    return xhr
            time.sleep(0.1)
        raise TimeoutError("Timeout waiting for HomeTimeline response")
    
    with sync_playwright() as pw:
        try: 
            # Khởi chạy trình duyệt Chromium ở chế độ có giao diện (headless=False)
            browser = pw.chromium.launch(headless=False)
            # Tạo context mới với kích thước viewport
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            # Tạo trang mới
            page = context.new_page()

            # Điều hướng đến trang x.com
            page.goto("https://x.com/i/flow/login", timeout=60000)
            
            
            print("======= Đang điều hướng đến trang login")
            
            page.wait_for_selector('input[name="text"]', timeout=10000)
            page.fill('input[name="text"]', "nnhvietanh@gmail.com")
            
            time.sleep(3)
            
            page.wait_for_selector('button:has-text("Next")', timeout=10000)
            page.click('button:has-text("Next")')
            
            time.sleep(3)
            
            page.wait_for_selector('input[name="text"]', timeout=10000)
            page.fill('input[name="text"]', "@kevinninh200496")
            
            time.sleep(3)
            
            page.wait_for_selector('button:has-text("Next")', timeout=10000)
            page.click('button:has-text("Next")')
            
            time.sleep(3)
            
            page.wait_for_selector('input[name="password"]', timeout=10000)
            page.fill('input[name="password"]', "@Vietanh96")

            time.sleep(3)

            
            page.wait_for_selector('button:has-text("Log in")', timeout=10000)
            page.click('button:has-text("Log in")')
            
            page.on("response", intercept_response) 
            page.wait_for_selector("[data-testid='tweet']")

            # Đợi 5 giây
            time.sleep(10)
            
            # go to url and wait for the page to load
            # page.wait_for_selector("[data-testid='tweet']")

            response = wait_for_user_tweets(page, timeout=30000)
            print(response.json())


            # Đóng trình duyệt
            browser.close()
        except Exception as e:
            print(e)
            
            
            