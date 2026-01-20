import requests, time
from datetime import datetime 

# MISC
MAX_RETRIES = 20
RETRY_DELAY = 2

def send_request_with_retry(
    url, headers=None, json_data=None, method="post", max_retries=3
):
    for attempt in range(max_retries):
        try:
            if method == "patch":
                response = requests.patch(url, headers=headers, json=json_data)
            elif method == "post":
                response = requests.post(url, headers=headers, json=json_data)
            elif method == "get":
                response = requests.get(url)

            response.raise_for_status()  # 如果响应状态码不是200系列，则抛出HTTPError异常
            return response
        
        except requests.exceptions.HTTPError as e:
            # HTTP 错误（4xx, 5xx）
            print(f"Request Exception occurred: <{e}> .Error: {e.response.text}")
            if attempt < max_retries - 1:
                print(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise
        
        except requests.exceptions.RequestException as e:
            # 其他网络错误（SSL, 超时等）
            print(f"Request Exception occurred: <{e}>")
            if attempt < max_retries - 1:
                print(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise
        
        except Exception as e:
            # 未预期的错误
            print(f"Unexpected error: <{e}>")
            raise

def parse_steam_date(text: str): 
    text = text.strip() 
    if text.lower() in ["coming soon", "tba"]: 
        return None
    formats = [ "%Y 年 %m 月 %d 日", "%d %b, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y", ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None