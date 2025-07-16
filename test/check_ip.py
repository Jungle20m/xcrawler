import requests
import json

def get_public_ip_with_proxy():
    # Cấu hình proxy (nếu có)
    proxies = {
        "http": "http://username:password@proxy_host:proxy_port",
        "https": "http://username:password@proxy_host:proxy_port"
    }
    # Ví dụ: proxies = {"http": "http://user:pass@10.10.1.10:3128", "https": "http://user:pass@10.10.1.10:3128"}

    # URL để kiểm tra IP công khai
    ip_check_url = "https://api.ipify.org?format=json"

    try:
        # Gửi request để lấy IP
        response = requests.get(ip_check_url, timeout=10)
        response.raise_for_status()
        ip_data = response.json()
        public_ip = ip_data["ip"]
        print(f"IP của máy/proxy khi gửi request: {public_ip}")

        # # Gửi request đến URL GetUser (thay bằng URL thực tế)
        # getuser_url = "https://example.com/api/GetUser"
        # response = requests.get(getuser_url, proxies=proxies, timeout=10)
        # response.raise_for_status()

        # # Lấy header và cookies
        # print("Request Headers:", json.dumps(dict(response.request.headers), indent=2))
        # print("Request Cookies:", json.dumps(response.request._cookies.get_dict(), indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi request: {str(e)}")

# Chạy hàm
get_public_ip_with_proxy()