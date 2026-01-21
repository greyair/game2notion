# -*- coding: utf-8 -*-
"""
Steam API 相关函数
"""

import requests
import time
from bs4 import BeautifulSoup
from urllib import request
from http import cookiejar

# ==================== STEAM API ====================
def get_owned_games_from_steam(steam_api_key, steam_user_id, include_played_free_games=True):
    """获取 Steam 所有游戏"""
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
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


def get_steam_recent_games(steam_api_key, steam_user_id, count=300):
    """获取最近游玩的游戏（包含游玩时间）"""
    url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
    params = {
        "key": steam_api_key,
        "steamid": steam_user_id,
        "count": count,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("response", {})
        games = data.get("games", [])
        print(f"✓ 从 Steam 获取最近游玩列表成功，数量: {len(games)}")
        return games
    except Exception as e:
        print(f"✗ 从 Steam 获取最近游玩失败: {e}")
        return []


def get_achievements_from_steam(game, steam_api_key, steam_user_id):
    """获取游戏成就数据"""
    url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
    params = {
        "key": steam_api_key,
        "steamid": steam_user_id,
        "appid": game["appid"]
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        # 4xx 错误表示无成就数据
        if 400 <= response.status_code < 500:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⊘ 获取 {game['name']} 成就失败: {e}")
        return None


def parse_achievements_info(game_achievements):
    """解析成就信息"""
    info = {"total": -1, "achieved": -1, "earliest_unlock": None}
    
    # 无数据或查询失败
    if not game_achievements or not game_achievements.get("playerstats", {}).get("success"):
        return info
    
    # 游戏无成就
    achievements = game_achievements["playerstats"].get("achievements", [])
    if not achievements:
        return info
    
    # 计算成就统计
    total = len(achievements)
    achieved = sum(1 for a in achievements if a.get("achieved") == 1)
    unlock_times = [a["unlocktime"] for a in achievements 
                   if a.get("achieved") == 1 and a.get("unlocktime", 0) > 0]
    
    return {
        "total": total,
        "achieved": achieved,
        "earliest_unlock": min(unlock_times) if unlock_times else None
    }


# ==================== STEAM STORE ====================
def get_steam_review_info(appid, userid):
    """获取用户对游戏的评论"""
    url = f"https://steamcommunity.com/profiles/{userid}/recommended/{appid}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        req = request.Request(url, headers=headers)
        with request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        soup = BeautifulSoup(html, 'html.parser')
        review_elem = soup.find('div', {'id': 'ReviewText'})
        return review_elem.get_text(strip=True) if review_elem else ""
    except Exception:
        return ""


def _setup_steam_cookies(country="CN", language="schinese"):
    """设置 Steam 请求的 Cookie 和 Headers"""
    cookies = {
        'birthtime': '568022401',
        'lastagecheckage': '1-January-1990',
        'wants_mature_content': '1',
        'Steam_Language': language,
        'steamCountry': country
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
    headers['Cookie'] = cookie_str
    
    return headers


def get_steam_store_info(appid, country="CN", language="schinese"):
    """获取 Steam 商店游戏信息"""
    url = f"https://store.steampowered.com/app/{appid}/?l={language}&cc={country}"
    headers = _setup_steam_cookies(country, language)
    
    default_info = {
        'game_name': '',
        'genres': [],
        'developers': [],
        'publishers': [],
        'release_date': '',
        'info': '',
        'price': '',
        'review': '',
        'tag': [],
        'app_icon': '',
        'header_image': ''
    }
    
    try:
        req = request.Request(url, headers=headers)
        with request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"✗ 请求失败 AppID {appid}: {e}")
        return default_info
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取各种信息
    game_name = _get_game_name(soup)
    genres, developers, publishers, release_date = _get_game_details(soup)
    info = _get_game_description(soup)
    price = _get_game_price(soup)
    review = _get_game_review(soup)
    tags = _get_game_tags(soup)
    app_icon = _get_game_app_icon(soup)
    header_image = _get_game_header_image(soup)
    
    return {
        'game_name': game_name,
        'genres': genres,
        'developers': developers,
        'publishers': publishers,
        'release_date': release_date,
        'info': info,
        'price': price,
        'review': review,
        'tag': tags,
        'app_icon': app_icon,
        'header_image': header_image
    }


# ==================== STEAM STORE 详情提取 ====================
def _get_game_name(soup):
    """提取游戏名称"""
    try:
        elem = soup.find('div', {'class': 'apphub_AppName'})
        return elem.get_text(strip=True) if elem else ''
    except Exception:
        return ''


def _get_game_app_icon(soup):
    """提取游戏应用图标"""
    try:
        icon_container = soup.find('div', {'class': 'apphub_AppIcon'})
        if icon_container:
            icon_img = icon_container.find('img')
            return icon_img.get('src', '') if icon_img else ''
        return ''
    except Exception:
        return ''


def _get_game_header_image(soup):
    """提取游戏 Header 图片"""
    try:
        header_img = soup.find('img', {'class': 'game_header_image_full'})
        return header_img.get('src', '') if header_img else ''
    except Exception:
        return ''


def _get_game_description(soup):
    """提取游戏描述"""
    try:
        elems = soup.find_all('div', {'class': 'game_description_snippet'})
        return elems[0].get_text(strip=True) if elems else ''
    except Exception:
        return ''


def _get_game_tags(soup):
    """提取游戏标签"""
    try:
        tags = [tag.get_text(strip=True) for tag in soup.find_all('a', {'class': 'app_tag'})[:8]]
        return tags
    except Exception:
        return []


def _get_game_price(soup):
    """提取游戏价格"""
    try:
        elem = soup.select_one(".game_area_purchase_game .game_purchase_price")
        return elem.get_text(strip=True) if elem else ''
    except Exception:
        return ''


def _get_game_review(soup):
    """提取游戏评分"""
    try:
        elem = soup.select_one(".user_reviews_summary_row .game_review_summary")
        return elem.get_text(strip=True) if elem else ''
    except Exception:
        return ''


def _get_game_details(soup):
    """提取游戏详情（类型、开发商、发行商、发行日期）"""
    genres, developers, publishers, release_date = [], [], [], ''
    
    try:
        detail = soup.find("div", id="genresAndManufacturer")
        if not detail:
            return genres, developers, publishers, release_date
        
        # 获取类型
        genres = [a.get_text(strip=True) 
                 for a in detail.select('b:-soup-contains("类型") ~ span a')]
        
        # 获取开发商
        dev_label = detail.find("b", string=lambda s: s and "开发者" in s)
        if dev_label:
            developers = [a.get_text(strip=True).replace(',', '_') for a in dev_label.find_next_siblings("a")]
        
        # 获取发行商
        pub_label = detail.find("b", string=lambda s: s and "发行商" in s)
        if pub_label:
            publishers = [a.get_text(strip=True).replace(',', '_') for a in pub_label.find_next_siblings("a")]
        
        # 获取发行日期
        date_label = detail.find("b", string=lambda s: s and "发行日期" in s)
        if date_label:
            text = date_label.find_next_sibling(string=True)
            release_date = text.strip() if text else ''
    
    except Exception as e:
        print(f"✗ 获取游戏详情失败 AppID: {e}")
    
    return genres, developers, publishers, release_date