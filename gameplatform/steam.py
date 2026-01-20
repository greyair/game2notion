from bs4 import BeautifulSoup
from urllib import request, parse
from http import cookiejar
import requests, time
from utils import send_request_with_retry

'''
https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key=***REMOVED***&steamid=***REMOVED***&format=json
'''


# steamapi
def get_owned_game_data_from_steam(steam_api_key, steam_user_id, include_played_free_games="true"):
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?"
    url = url + "key=" + steam_api_key
    url = url + "&steamid=" + steam_user_id
    url = url + "&include_appinfo=True"
    if include_played_free_games == "true":
        url = url + "&include_played_free_games=True"

    print("fetching data from steam..")

    try:
        response = send_request_with_retry(url, method="get")
        print("fetching data success!")
        return response.json()
    except Exception as e:
        print(f"Failed to send request: {e},Error: {response.text}")

def get_steam_achievements_count(game, steam_api_key, steam_user_id):
    game_achievements = query_achievements_info_from_steam(game, steam_api_key, steam_user_id)
    achievements_info = {}
    achievements_info["total"] = 0
    achievements_info["achieved"] = 0
    achievements_info["earliest_unlock"] = None

    if game_achievements is None or game_achievements["playerstats"]["success"] is False:
        achievements_info["total"] = -1
        achievements_info["achieved"] = -1
        print(f"no info for game {game['name']}")

    elif "achievements" not in game_achievements["playerstats"]:
        achievements_info["total"] = -1
        achievements_info["achieved"] = -1
        print(f"no achievements for game {game['name']}")

    else:
        achievments_array = game_achievements["playerstats"]["achievements"]
        total = len(achievments_array)
        unlocked = sum(1 for a in achievments_array if a.get('achieved', 0) == 1)
        unlocked_times = [a['unlocktime'] for a in achievments_array if a.get('achieved') == 1 and a.get('unlocktime', 0) > 0]
        earliest_unlock = min(unlocked_times) if unlocked_times else None
        achievements_info["total"] = total
        achievements_info["achieved"] = unlocked
        achievements_info["earliest_unlock"] = earliest_unlock

        print(f"{game['name']} achievements count complete!")

    return achievements_info

def query_achievements_info_from_steam(game, steam_api_key, steam_user_id):
    url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?"
    url = url + "key=" + steam_api_key
    url = url + "&steamid=" + steam_user_id
    url = url + "&appid=" + f"{game['appid']}"
    print(f"querying for {game['name']} achievements counts...")

    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查HTTP错误状态码（非2XX/3XX会抛出异常）
        return response.json()
    except requests.exceptions.RequestException as e:
        # 捕获所有requests库抛出的异常（如连接错误、超时、HTTP错误等）
        print(f"Request failed for {game['name']}: {str(e)} .Error: {response.text}")
    except ValueError as e:
        # 捕获JSON解析错误（如返回非JSON数据）
        print(f"Failed to parse JSON response for {game['name']}: {str(e)} .Error: {response.text}")

    return None


def get_steam_review_info(appid,userid):
    # 构造请求 URL 和 Headers
    url = f"https://steamcommunity.com/profiles/{userid}/recommended/{appid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    req = request.Request(url, headers=headers)

    try:
        with request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        #print(f"请求失败: AppID {appid}, 错误: {e}")
        return ''

    soup = BeautifulSoup(html, 'html.parser')
    review_text = ''

    try:
        review_text_element = soup.find('div', {'id': 'ReviewText'})
        if review_text_element:
            review_text = review_text_element.get_text(strip=True)
    except Exception as e:
        #print(f"游戏名提取失败: AppID {appid}, 错误: {e}")
        return ''

    return review_text

def get_steam_store_info(appid):
    # 构造请求 URL 和 Headers
    url = f"https://store.steampowered.com/app/{appid}/?l=schinese"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    # 设置 Cookies（用于绕过年龄验证）
    cj = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cj))
    request.install_opener(opener)

    # 手动添加 Cookie
    cookies = {
        'birthtime': '568022401',
        'lastagecheckage': '1-January-1990',
        'wants_mature_content': '1'
    }

    cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
    headers['Cookie'] = cookie_str

    # 创建请求
    req = request.Request(url, headers=headers)

    metainfo = {
        'info': '',
        'tag': []
    }

    try:
        with request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"请求失败: AppID {appid}, 错误: {e}")
        return metainfo

    soup = BeautifulSoup(html, 'html.parser')

    # game_name
    try:
        title_tag = soup.find('div', {'class': 'apphub_AppName'})
        game_name = title_tag.get_text(strip=True) if title_tag else ''
    except Exception as e:
        game_name = ''
        
    # tags
    try:
        tags = [tag.get_text(strip=True) for tag in soup.find_all('a', {'class': 'app_tag'})[:8]]
    except Exception as e:
        tags = []
        
    # info
    try:
        info_elements = soup.find_all('div', {'class': 'game_description_snippet'})
        info_text = info_elements[0].get_text(strip=True) if info_elements else ''
    except Exception as e:
        info_text = ''
        
    # detail
    try:
        details = soup.select_one("#genresAndManufacturer")
        if details:
            eng_name = details.find("b", string=lambda s: s and "名称" in s).find_next_siblings(string=True).strip() if details.find("b", string=lambda s: s and "名称" in s) else ''
            genres = [a.get_text(strip=True) for a in details.find("b", string=lambda s: s and "类型" in s).find_next_siblings("a")] if details.find("b", string=lambda s: s and "类型" in s) else []
            developers = [a.get_text(strip=True) for a in details.find("b", string=lambda s: s and "开发者" in s).find_next_siblings("a")] if details.find("b", string=lambda s: s and "开发者" in s) else []
            publishers = [a.get_text(strip=True) for a in details.find("b", string=lambda s: s and "发行商" in s).find_next_siblings("a")] if details.find("b", string=lambda s: s and "发行商" in s) else []
            release_date = details.find("b", string=lambda s: s and "发行日期" in s).find_next_siblings(string=True).strip() if details.find("b", string=lambda s: s and "发行日期" in s) else ''
        else:
            eng_name, genres, developers, publishers, release_date = '', [], [], [], ''
    except Exception as e:
        print(f"获取游戏详情失败 AppID {appid}: {e}")
        eng_name, genres, developers, publishers, release_date = '', [], [], [], ''
        
    # price
    try:
        prices = soup.select(".game_purchase_price, .discount_final_price") 
        price_text = [p.get_text(strip=True) for p in prices]
    except Exception as e:
        price_text = ''
        
    # review 
    try:
        review_summary = soup.select_one(".user_reviews_summary_row .game_review_summary") 
        review_text = review_summary.get_text(strip=True) if review_summary else None
    except Exception as e:
        review_text = ''

    metainfo = {
        'game_name': game_name,
        'eng_name': eng_name,
        'genres': genres,
        'developers': developers,
        'publishers': publishers,
        'release_date': release_date,
        'info': info_text,
        'price': price_text,
        'review': review_text,
        'tag': tags
    }
    return metainfo


