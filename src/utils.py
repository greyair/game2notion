import logging
import requests
import time
from datetime import datetime

# MISC
MAX_RETRIES = 20
RETRY_DELAY = 2

_logger = logging.getLogger(__name__)


def get_logger(name=None):
    """获取 logger（统一入口，便于复用日志配置）"""
    return logging.getLogger(name)


def send_request_with_retry(
    url,
    headers=None,
    json_data=None,
    method="post",
    retries=MAX_RETRIES,
    retry_delay=RETRY_DELAY,
    timeout=10,
):
    """统一的请求函数（带重试和指数退避）"""
    for attempt in range(retries):
        try:
            method_lower = method.lower()
            if method_lower == "patch":
                response = requests.patch(url, headers=headers, json=json_data, timeout=timeout)
            elif method_lower == "post":
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method_lower == "get":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            _logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # 指数退避
            else:
                _logger.error(f"Max retries exceeded for {url}")
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


def format_notion_multi_select(value):
    """
    处理 multi_select 类型数据
    支持：
      - None / ""              -> []
      - "A, B"                 -> [{"name": "A"}, {"name": "B"}]
      - ["A", "B, C"]          -> [{"name": "A"}, {"name": "B"}, {"name": "C"}]
      - ["A", "B", "C"]        -> [{"name": "A"}, {"name": "B"}, {"name": "C"}]
    """
    if not value:
        return []

    if isinstance(value, str):
        value = [value]

    items = [
        x.strip()
        for s in value
        for x in (s.split(",") if isinstance(s, str) else [s])
        if str(x).strip()
    ]

    return [{"name": item} for item in items]