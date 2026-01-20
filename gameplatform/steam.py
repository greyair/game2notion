from bs4 import BeautifulSoup
from urllib import request, parse
from http import cookiejar
import requests, time
from utils import send_request_with_retry

'''
https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key=***REMOVED***&steamid=***REMOVED***&format=json
'''

# ==================== STEAM API ====================
def get_owned_games_from_steam(steam_api_key, steam_user_id, include_played_free_games="true"):
    """获取 Steam 所有游戏"""
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": steam_api_key,
        "steamid": steam_user_id,
        "include_appinfo": "True",
        "include_played_free_games": "True" if include_played_free_games else "False"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        print("✓ 从 Steam 获取游戏列表成功")
        return response.json().get("response", {}).get("games", [])
    except Exception as e:
        print(f"✗ 从 Steam 获取游戏失败: {e}")
        return []


def get_achievements_from_steam(game, steam_api_key, steam_user_id):
    """获取游戏成就"""
    url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
    params = {
        "key": steam_api_key,
        "steamid": steam_user_id,
        "appid": game["appid"]
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        # 4xx 状态码不抛出异常，直接返回 None
        if 400 <= response.status_code < 500:
            print(f"{game['name']} has no achievements data")
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⊘ 获取 {game['name']} 成就失败: {e}")
        return None

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
        # 4xx 状态码不抛出异常，直接返回 None
        if 400 <= response.status_code < 500:
            print(f"{game['name']} has no achievements data")
            return None
        response.raise_for_status()
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
    url = f"https://store.steampowered.com/app/{appid}/?l=schinese&cc=cn"
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
        'wants_mature_content': '1',
        'Steam_Language': 'schinese',
        'steamCountry': 'CN'
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
    
    # app_icon
    try:
        icon_img = soup.find('div', {'class': 'apphub_AppIcon'}).find('img')
        app_icon = icon_img.get('src', '') if icon_img else ''
    except Exception as e:
        app_icon = ''
    
    # header_image
    try:
        header_img = soup.find('img', {'class': 'game_header_image_full'})
        header_image = header_img.get('src', '') if header_img else ''
    except Exception as e:
        header_image = ''
        
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
        detail = soup.find("div", id="genresAndManufacturer")
        if detail:
            #eng_name = detail.find("b", string=lambda s: s and "名称" in s).find_next_sibling(string=True).strip()if detail else ''
            genres = [a.get_text(strip=True) for a in detail.select('b:-soup-contains("类型") ~ span a')] if detail else []
            developers = [a.get_text(strip=True) for a in detail.find("b", string=lambda s: s and "开发者" in s).find_next_siblings("a")] if detail.find("b", string=lambda s: s and "开发者" in s) else []
            publishers = [a.get_text(strip=True) for a in detail.find("b", string=lambda s: s and "发行商" in s).find_next_siblings("a")] if detail.find("b", string=lambda s: s and "发行商" in s) else []
            release_date = detail.find("b", string=lambda s: s and "发行日期" in s).find_next_sibling(string=True).strip() if detail.find("b", string=lambda s: s and "发行日期" in s) else ''
        else:
            eng_name, genres, developers, publishers, release_date = '', [], [], [], ''
    except Exception as e:
        print(f"获取游戏详情失败 AppID {appid}: {e}")
        eng_name, genres, developers, publishers, release_date = '', [], [], [], ''
        
    # price
    try:
        #prices = soup.select(".game_purchase_price, .discount_final_price") 
        #price_text = [p.get_text(strip=True) for p in prices]
        price_tag = soup.select_one(".game_area_purchase_game .game_purchase_price")
        price = price_tag.get_text(strip=True) if price_tag else ''
    except Exception as e:
        price = ''
        
    # review 
    try:
        review_summary = soup.select_one(".user_reviews_summary_row .game_review_summary") 
        review_text = review_summary.get_text(strip=True) if review_summary else ''
    except Exception as e:
        review_text = ''
        
        
    store_url = f"https://store.steampowered.com/app/{appid}/"
    #icon_url = f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg"
    cover_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"

    metainfo = {
        'game_name': game_name,
        #'eng_name': eng_name,
        'genres': genres,
        'developers': developers,
        'publishers': publishers,
        'release_date': release_date,
        'info': info_text,
        'price': price,
        'review': review_text,
        'tag': tags,
        'app_icon': app_icon,
        'header_image': header_image
    }
    return metainfo


