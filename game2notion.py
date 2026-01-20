import argparse
import requests
import time
import os
import logging
from utils import send_request_with_retry, parse_steam_date
from gameplatform.steam import get_steam_review_info, get_owned_game_data_from_steam, get_steam_achievements_count
from gameplatform.steam1 import get_steam_store_info

# CONFIG
STEAM_API_KEY = os.environ.get("STEAM_API_KEY") or '***REMOVED***'
# get from https://steamcommunity.com/dev/apikey
STEAM_USER_ID = os.environ.get("STEAM_USER_ID") or '***REMOVED***'
# get from your steam profile https://steamcommunity.com/profiles/{STEAM_USER_ID}
NOTION_API_KEY = os.environ.get("NOTION_API_KEY") or '***REMOVED***'
# https://developers.notion.com/docs/create-a-notion-integration
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID") or '***REMOVED***'
# https://developers.notion.com/reference/retrieve-a-database
# OPTIONAL
include_played_free_games = os.environ.get("include_played_free_games") or 'true'
#set to 'true' by default
enable_item_update = os.environ.get("enable_item_update") or 'true'
#set to 'true' by default
enable_filter = os.environ.get("enable_filter") or 'false'
#set to 'false' by default 


# notionapi
def add_item_to_notion_database(game, achievements_info, review_text, steam_store_data):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    logger.info(f"adding game {game['name']} to notion...")

    playtime = round(float(game["playtime_forever"]) / 60, 1)
    last_played_time = {"start": time.strftime("%Y-%m-%d", time.localtime(game["rtime_last_played"]))} if game["rtime_last_played"] else None
    store_url = f"https://store.steampowered.com/app/{game['appid']}"
    icon_url = f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg"
    cover_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{game['appid']}/header.jpg"
    total_achievements = achievements_info["total"]
    achieved_achievements = achievements_info["achieved"]
    earliest_unlock = {"start": time.strftime("%Y-%m-%d", time.localtime(achievements_info["earliest_unlock"])) } if achievements_info["earliest_unlock"] else None
    release_date = {"start": parse_steam_date(steam_store_data['release_date']).isoformat()} if parse_steam_date(steam_store_data['release_date']) else None

    data = {
        "parent": {
            "type": "database_id",
            "database_id": f"{NOTION_DATABASE_ID}",
        },
        "properties": {
            "游戏名称": {"type": "title","title": [{"type": "text", "text": {"content": f"{game['name']}"}}]},
            "游戏商品名": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": f"{steam_store_data['game_name']}"}}]},
            "游戏时长": {"type": "number", "number": playtime},
            "游戏类型": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['genres'])},
            "开发商": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['developers'])},
            "发行商": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['publishers'])},
            "发行日期": {"type": "date", "date": release_date},
            "上次游玩时间": {"type": "date", "date": last_played_time},
            "商店链接": {"type": "url", "url": store_url},
            "成就总数": {"type": "number", "number": total_achievements},
            "获得成就": {"type": "number", "number": achieved_achievements},
            "成就首次解锁": {"type": "date", "date": earliest_unlock},
            "游戏简介": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": steam_store_data["info"]}}]},
            "游戏标签": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['tag'])},
            "游戏平台": {"type": "select", "select": {"name": "Steam"}},
            "商店价格": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": steam_store_data["price"]}}]},
            "玩家评分": {"type": "select", "select": {"name": steam_store_data["review"]}},
            "appid": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": f"{game['appid']}"}}]},
        },
        "cover": {"type": "external", "external": {"url": cover_url}},
        "icon": {"type": "external", "external": {"url": icon_url}},
    }

    try:
        response = send_request_with_retry(
            url, headers=headers, json_data=data, method="post"
        )
        logger.info(f"{game['name']} added!")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send request: {e} .Error: {response.text}")

def query_notion_games():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    notion_games = {}  # {(eng_name, platform): {"last_played": ...}}
    has_more = True
    next_cursor = None

    while has_more:
        data = {"page_size": 100}
        if next_cursor:
            data["start_cursor"] = next_cursor

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        for page in result["results"]:
            props = page.get("properties", {})
            try:
                # 读取游戏名
                game_name = props.get("游戏名称", {}).get("title", [])
                if not game_name:
                    continue
                name = game_name[0]["plain_text"]

                # 读取游戏平台
                platform_info = props.get("游戏平台", {}).get("select", {})
                platform = platform_info.get("name") if platform_info else "Unknown"

                # 读取上次游玩时间
                date_info = props.get("上次游玩时间", {}).get("date", {})
                last_played = date_info.get("start") if date_info else None

                # 用 (游戏名, 平台) 作为键
                key = (name, platform)
                notion_games[key] = last_played
            except Exception as e:
                logger.warning(f"跳过一项，读取失败：{e}")

        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")

    logger.info(f"共获取 Notion 中 {len(notion_games)} 项")
    return notion_games

def query_item_from_notion_database(game):
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    logger.info(f"querying {game['name']} from database")
    data = {"filter": {"property": "name", "rich_text": {"equals": f"{game['name']}"}}}

    try:
        response = send_request_with_retry(
            url, headers=headers, json_data=data, method="post"
        )
        logger.info(f"query complete!")
    except Exception as e:
        logger.error(f"Failed to send request: {e} .Error: {response.text}")
    finally:
        return response.json()

def update_item_to_notion_database(page_id, game, achievements_info, review_text, steam_store_data):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    playtime = round(float(game["playtime_forever"]) / 60, 1)
    last_played_time = time.strftime(
        "%Y-%m-%d", time.localtime(game["rtime_last_played"])
    )
    store_url = f"https://store.steampowered.com/app/{game['appid']}"
    icon_url = f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg"
    cover_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{game['appid']}/header.jpg"
    total_achievements = achievements_info["total"]
    achieved_achievements = achievements_info["achieved"]
    earliest_unlock = time.strftime("%Y-%m-%d", time.localtime(achievements_info["earliest_unlock"])) if achievements_info["earliest_unlock"] else ""

    if total_achievements > 0:
        completion = round(
            float(achieved_achievements) / float(total_achievements) * 100, 1
        )
    else:
        completion = -1

    logger.info(f"updating {game['name']} to notion...")

    data = {
        "properties": {
            "name": {
                "type": "title",
                "title": [{"type": "text", "text": {"content": f"{steam_store_data['game_name']}"}}],
            },
            "游戏商品名": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": f"{game['name']}"}},]},
            "游戏时长": {"type": "number", "number": playtime},
            "游戏类型": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['genres'])},
            "开发商": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['developers'])},
            "发行商": {"type": "multi_select", "multi_select": build_notion_multi_select(steam_store_data['publishers'])},
            "发行日期": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": f"{steam_store_data['release_date']}"}}, ]},
            "上次游玩时间": {"type": "date", "date": {"start": last_played_time}},
            "商店链接": {"type": "url","url": store_url },
            "成就总数": {"type": "number", "number": total_achievements},
            "获得成就": {"type": "number","number": achieved_achievements},
            "成就首次解锁": {"type": "date", "date": {"start": earliest_unlock}},
            "进度": {"type": "number", "number": completion},
            "游戏简介": { "type": "rich_text", "rich_text": [{"type": "text", "text": { "content": steam_store_data["info"] }}, ]},
            "游戏标签": {"type": "multi_select","multi_select": build_notion_multi_select(steam_store_data['tag'])},
            "appid": {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": f"{game['appid']}"}}],},
        },
        "cover": {"type": "external", "external": {"url": f"{cover_url}"}},
        "icon": {"type": "external", "external": {"url": f"{icon_url}"}},
    }

    try:
        response = send_request_with_retry(
            url, headers=headers, json_data=data, method="patch"
        )
        logger.info(f"{game['name']} updated!")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send request: {e} .Error: {response.text}")


def database_create(page_id):
    url = "https://api.notion.com/v1/databases/"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    data = {
        "parent": {
            "type": "page_id",
            "page_id": page_id,
        },
        "title": [{"type": "text", "text": {"content": "Game List"}}],
        "properties": {
            "name": {"title": {}},
            "completion": {"number": {}},
            "playtime": {"number": {}},
            "last play": {"date": {}},
            "total achievements": {"number": {}},
            "achieved achievements": {"number": {}},
            "store url": {"url": {}},
        },
    }

    try:
        response = send_request_with_retry(
            url, headers=headers, json_data=data, method="post"
        )
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send request: {e} .Error: {response.text}")


# MISC
def is_record(game, achievements):
    not_record_time = "2020-01-01 00:00:00"
    time_tuple = time.strptime(not_record_time, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(time_tuple)
    playtime = round(float(game["playtime_forever"]) / 60, 1)

    if (playtime < 0.1 and achievements["total"] < 1) or (
        game["rtime_last_played"] < timestamp
        and achievements["total"] < 1
        and playtime < 6
    ):
        logger.info(f"{game['name']} does not meet filter rule!")
        return False

    return True

def constract_notion_multi_select_property(tags):
    #color = ['blue','brown','gray','green','orange','pink','purple','red','yellow']
    options = []

    for tag in tags:
        option = {}
        option['name'] = tag
        #option['color'] = color[hash(tag) % len(color)]
        options.append(option)

    return options

def build_notion_multi_select(value):
    """
    value 支持：
      - None / ""              -> 清空
      - "A, B"                 -> ["A", "B"]
      - ["A", "B, C"]          -> ["A", "B", "C"]
      - ["A", "B", "C"]        -> 原样
    """
    if not value: return []

    if isinstance(value, str):
        value = [value]
    items = [
        x.strip()
        for s in value
        for x in (s.split(",") if isinstance(s, str) else [s])
        if str(x).strip()
    ]
    return [{"name": item} for item in items]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='启用调试日志输出')
    args = parser.parse_args()

    # 配置日志
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)

    # 移除所有现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    if args.debug:
        # 添加文件处理器
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    notion_games = query_notion_games()
    test = get_steam_store_info(34330)
    owned_game_steam = get_owned_game_data_from_steam(STEAM_API_KEY, STEAM_USER_ID, include_played_free_games)

    if len(owned_game_steam["response"]) == 0 or owned_game_steam["response"]["games"] == []:
        logger.error("no owned game data found! exiting...")
        exit(1)
    for game in owned_game_steam["response"]["games"]:
        is_add = True
        achievements_info = {}
        achievements_info = get_steam_achievements_count(game, STEAM_API_KEY, STEAM_USER_ID)
        #review_text = get_steam_review_info(game["appid"], STEAM_USER_ID)
        steam_store_data = get_steam_store_info(game["appid"])

        if "rtime_last_played" not in game:
            logger.info(f"{game['name']} have no last play time! setting to 0!")
            game["rtime_last_played"] = 0

        if enable_filter == "true" and is_record(game, achievements_info) == False:
            continue

        # 用 (英文名, 平台) 作为键查找
        game_key = (game["name"], "Steam")
        
        if game_key not in notion_games:
            logger.info(f"{game['name']} does not exist! creating new item!")
            print(f"Adding {game['name']} to Notion database...")
            add_item_to_notion_database(game, achievements_info, '', steam_store_data)
        else:
            if enable_item_update == "true":
                logger.info(f"{game['name']} already exists! updating!")
            else:
                logger.info(f"{game['name']} already exists! skipping!")
            print(f"Updating {game['name']} in Notion database...")
        time.sleep(5)  # 避免请求过快

