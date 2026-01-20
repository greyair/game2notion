# -*- coding: utf-8 -*-
"""
Steam 游戏信息同步到 Notion
"""

import argparse
import requests
import time
import logging
from datetime import datetime
from config import (
    STEAM_API_KEY, STEAM_USER_ID, NOTION_API_KEY, NOTION_GAMES_DATABASE_ID,
    NOTION_PROPERTIES, include_played_free_games, enable_item_update, enable_filter, MAX_RETRIES, RETRY_DELAY,
    get_property_name
)
from platforms.steam import (
    get_owned_games_from_steam, get_achievements_from_steam, 
    parse_achievements_info, get_steam_store_info
)

logger = logging.getLogger(__name__)


# ==================== UTILS ====================
def build_notion_multi_select(value):
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


def send_request_with_retry(url, headers=None, json_data=None, method="get", retries=MAX_RETRIES):
    """统一的请求函数"""
    for attempt in range(retries):
        try:
            if method.lower() == "get":
                response = requests.get(url, timeout=10)
            elif method.lower() == "post":
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
            elif method.lower() == "patch":
                response = requests.patch(url, headers=headers, json=json_data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (2 ** attempt))  # 指数退避
            else:
                logger.error(f"Max retries exceeded for {url}")
                raise


# ==================== DATA TRANSFORM ====================
def parse_steam_date(date_str):
    """解析 Steam 日期字符串"""
    if not date_str:
        return None
    try:
        # 处理格式: "2025 年 5 月 30 日"
        return datetime.strptime(date_str, "%Y 年 %m 月 %d 日").date()
    except Exception:
        try:
            # 尝试其他格式
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except Exception:
            logger.warning(f"无法解析日期: {date_str}")
            return None


def build_game_properties(game, achievements_info, steam_store_data):
    """构建游戏属性数据 - 使用配置文件中的属性名和统一的处理方法"""
    playtime = round(float(game.get("playtime_forever", 0)) / 60, 1)
    
    # 处理时间戳为日期字符串（仅当有值时）
    last_played_time = datetime.fromtimestamp(game["rtime_last_played"]).strftime("%Y-%m-%d") if game.get("rtime_last_played") else None
    earliest_unlock = achievements_info.get("earliest_unlock")
    earliest_unlock_time = datetime.fromtimestamp(earliest_unlock).strftime("%Y-%m-%d") if earliest_unlock else None
    
    # 处理发行日期（仅当能解析时）
    release_date_str = steam_store_data.get("release_date", "")
    release_date = parse_steam_date(release_date_str)
    
    total_achievements = achievements_info.get("total", -1)
    achieved_achievements = achievements_info.get("achieved", -1)
    
    # 构建属性字典
    props = {}
    
    # ========== 基础信息 ==========
    props[get_property_name("name")] = {
        "type": "title",
        "title": [{"type": "text", "text": {"content": game["name"]}}]
    }
    
    props[get_property_name("game_name")] = {
        "type": "rich_text",
        "rich_text": [{"type": "text", "text": {"content": steam_store_data.get("game_name", "")}}]
    }
    
    props[get_property_name("appid")] = {
        "type": "rich_text",
        "rich_text": [{"type": "text", "text": {"content": str(game["appid"])}}]
    }
    
    # ========== 数值字段 ==========
    props[get_property_name("playtime")] = {
        "type": "number",
        "number": playtime
    }
    
    props[get_property_name("total_achievements")] = {
        "type": "number",
        "number": total_achievements
    }
    
    props[get_property_name("achieved_achievements")] = {
        "type": "number",
        "number": achieved_achievements
    }
    
    # ========== 日期字段（仅当有值时才添加） ==========
    if last_played_time:
        props[get_property_name("last_play")] = {
            "type": "date",
            "date": {"start": last_played_time}
        }
    
    if earliest_unlock_time:
        props[get_property_name("earliest_unlock")] = {
            "type": "date",
            "date": {"start": earliest_unlock_time}
        }
    
    if release_date:
        props[get_property_name("release_date")] = {
            "type": "date",
            "date": {"start": release_date.isoformat()}
        }
    
    # ========== 分类字段 ==========
    genres = build_notion_multi_select(steam_store_data.get("genres", []))
    if genres:
        props[get_property_name("genres")] = {
            "type": "multi_select",
            "multi_select": genres
        }
    
    developers = build_notion_multi_select(steam_store_data.get("developers", []))
    if developers:
        props[get_property_name("developers")] = {
            "type": "multi_select",
            "multi_select": developers
        }
    
    publishers = build_notion_multi_select(steam_store_data.get("publishers", []))
    if publishers:
        props[get_property_name("publishers")] = {
            "type": "multi_select",
            "multi_select": publishers
        }
    
    tags = build_notion_multi_select(steam_store_data.get("tag", []))
    if tags:
        props[get_property_name("tags")] = {
            "type": "multi_select",
            "multi_select": tags
        }
    
    # ========== 文本字段 ==========
    props[get_property_name("info")] = {
        "type": "rich_text",
        "rich_text": [{"type": "text", "text": {"content": steam_store_data.get("info", "")}}]
    }
    
    price = steam_store_data.get("price", "")
    props[get_property_name("price")] = {
        "type": "rich_text",
        "rich_text": [{"type": "text", "text": {"content": price}}]
    }
    
    # ========== 选择字段 ==========
    props[get_property_name("platform")] = {
        "type": "select",
        "select": {"name": "Steam"}
    }
    
    review = steam_store_data.get("review", "")
    if review:
        props[get_property_name("review")] = {
            "type": "select",
            "select": {"name": review}
        }
    
    # ========== URL 字段 ==========
    store_url = f"https://store.steampowered.com/app/{game['appid']}"
    props[get_property_name("store_url")] = {
        "type": "url",
        "url": store_url
    }
    
    return props


def build_page_data(game, achievements_info, steam_store_data, is_update=False):
    """构建 Notion page 数据"""
    properties = build_game_properties(game, achievements_info, steam_store_data)
    
    data = {"properties": properties}
    
    # 新增时添加 cover, icon, parent
    if not is_update:
        if steam_store_data.get("header_image"):
            cover_url = steam_store_data["header_image"]
        else:
            cover_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{game['appid']}/header.jpg"
        if steam_store_data.get("app_icon"):
            icon_url = steam_store_data["app_icon"]
        else:
            icon_url = f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg"
        
        data.update({
            "parent": {"type": "database_id", "database_id": NOTION_GAMES_DATABASE_ID},
            "cover": {"type": "external", "external": {"url": cover_url}},
            "icon": {"type": "external", "external": {"url": icon_url}}
        })
    
    return data


# ==================== NOTION API ====================
def query_all_games_from_notion():
    """一次性查询 Notion 中所有游戏"""
    url = f"https://api.notion.com/v1/databases/{NOTION_GAMES_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    games_map = {}  # {game_name: {"page_id": ..., "last_play": ...}}
    has_more = True
    next_cursor = None
    
    name_prop = get_property_name("name")
    last_play_prop = get_property_name("last_play")
    platform_prop = get_property_name("platform")
    
    while has_more:
        data = {"page_size": 100}
        if next_cursor:
            data["start_cursor"] = next_cursor
        
        try:
            response = send_request_with_retry(url, headers=headers, json_data=data, method="post")
            result = response.json()
            
            for page in result.get("results", []):
                props = page.get("properties", {})
                try:
                    name_prop_data = props.get(name_prop, {}).get("title", [])
                    if not name_prop_data:
                        continue
                    
                    game_name = name_prop_data[0]["plain_text"]
                    page_id = page["id"]
                    
                    last_play_data = props.get(last_play_prop, {}).get("date", {})
                    last_play = last_play_data.get("start") if last_play_data else None
                    # 读取游戏平台
                    platform_info = props.get(platform_prop, {}).get("select", {})
                    platform = platform_info.get("name") if platform_info else "Unknown"
                    
                    key = (game_name, platform)
                    games_map[key] = {
                        "page_id": page_id,
                        "last_play": last_play
                    }
                except Exception as e:
                    logger.warning(f"解析游戏信息失败: {e}")
            
            has_more = result.get("has_more", False)
            next_cursor = result.get("next_cursor")
        
        except Exception as e:
            logger.error(f"查询 Notion 失败: {e}")
            break
    
    logger.info(f"✓ 获取 Notion 中 {len(games_map)} 个游戏")
    return games_map


def add_game_to_notion(game, achievements_info, steam_store_data):
    """添加游戏到 Notion"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    data = build_page_data(game, achievements_info, steam_store_data)
    
    try:
        response = send_request_with_retry(url, headers=headers, json_data=data, method="post")
        logger.info(f"✓ 已添加: {game['name']}")
        return True
    except Exception as e:
        logger.error(f"✗ 添加失败: {game['name']} - {e}")
        return False


def update_game_in_notion(page_id, game, achievements_info, steam_store_data):
    """更新游戏信息在 Notion"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    data = build_page_data(game, achievements_info, steam_store_data, is_update=True)
    
    try:
        response = send_request_with_retry(url, headers=headers, json_data=data, method="patch")
        logger.info(f"✓ 已更新: {game['name']}")
        return True
    except Exception as e:
        logger.error(f"✗ 更新失败: {game['name']} - {e}")
        return False


# ==================== FILTER ====================
def should_record_game(game, achievements_info):
    """判断是否记录该游戏"""
    if not enable_filter:
        return True
    
    playtime = round(float(game.get("playtime_forever", 0)) / 60, 1)
    last_played = game.get("rtime_last_played", 0)
    
    # 无游玩时间且无成就 -> 不记录
    if playtime < 0.1 and achievements_info["total"] < 1:
        return False
    
    # 长时间未玩且游玩时间少于6小时且无成就 -> 不记录
    week_ago = int(time.time()) - 7 * 86400
    if last_played < week_ago and playtime < 6 and achievements_info["total"] < 1:
        return False
    
    return True


# ==================== MAIN ====================
def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始同步 Steam 游戏到 Notion")
    logger.info("=" * 50)
    
    test = get_steam_store_info("387290", country="SG")
    
    # 获取 Steam 游戏列表
    games = get_owned_games_from_steam(STEAM_API_KEY, STEAM_USER_ID, include_played_free_games)
    if not games:
        logger.error("未获取到游戏列表")
        return
    
    # 一次性查询 Notion 中所有游戏
    notion_games_map = query_all_games_from_notion()
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    for idx, game in enumerate(games, 1):
        game_name = game["name"]
        logger.info(f"\n[{idx}/{len(games)}] 处理: {game_name}")
        
        achievements_data = get_achievements_from_steam(game, STEAM_API_KEY, STEAM_USER_ID)
        achievements_info = parse_achievements_info(achievements_data)
        steam_store_data = get_steam_store_info(game["appid"])
        if steam_store_data["tag"] == []:
            steam_store_data = get_steam_store_info(game["appid"], country="SG")
        
        # 在本地查找游戏
        game_key = (game_name, "Steam")
        notion_game = notion_games_map.get(game_key)
        
        if notion_game:
            # 游戏已存在 -> 更新
            if enable_item_update:
                page_id = notion_game["page_id"]
                last_play = notion_game["last_play"]
                logger.info(f"⊘ 上次游玩: {last_play}")
                game_last_played = datetime.fromtimestamp(game['rtime_last_played']).strftime("%Y-%m-%d") if game['rtime_last_played'] else None
                
                if last_play != game_last_played:
                    if update_game_in_notion(page_id, game, achievements_info, steam_store_data):
                        updated_count += 1
                else:
                    logger.info(f"⊘ 游玩时间未变更，跳过更新: {game_name}")
                    skipped_count += 1
            else:
                logger.info(f"⊘ 跳过更新: {game_name}")
                skipped_count += 1
        else:
            # 游戏不存在 -> 新增
            if add_game_to_notion(game, achievements_info, steam_store_data):
                added_count += 1
        
        time.sleep(0.3)  # API 限制
    
    logger.info("\n" + "=" * 50)
    logger.info(f"同步完成! 新增: {added_count}, 更新: {updated_count}, 跳过: {skipped_count}")
    logger.info("=" * 50)


def add_single_game_by_appid(appid):
    """通过 appid 添加或更新单个游戏"""
    logger.info("=" * 50)
    logger.info(f"开始处理游戏 (AppID: {appid})")
    logger.info("=" * 50)
    
    try:
        # 获取游戏的成就信息和商店信息
        achievements_data = get_achievements_from_steam({"appid": appid}, STEAM_API_KEY, STEAM_USER_ID)
        achievements_info = parse_achievements_info(achievements_data)
        steam_store_data = get_steam_store_info(appid)
        if steam_store_data["tag"] == []:
            steam_store_data = get_steam_store_info(appid, country="SG")
        
        game_name = steam_store_data.get("game_name", f"AppID_{appid}")
        if not game_name:
            logger.error(f"✗ 未找到 AppID {appid} 的游戏信息")
            return False
        
        # 构建基础游戏信息
        game = {
            "appid": appid,
            "name": game_name,
            "playtime_forever": 0,
            "rtime_last_played": 0,
            "img_icon_url": ""
        }
        
        # 查询 Notion 中的游戏
        notion_games_map = query_all_games_from_notion()
        game_key = (game_name, "Steam")
        notion_game = notion_games_map.get(game_key)
        
        if notion_game:
            # 游戏已存在 -> 强制更新
            logger.info(f"游戏已存在于 Notion，执行强制更新: {game_name}")
            page_id = notion_game["page_id"]
            if update_game_in_notion(page_id, game, achievements_info, steam_store_data):
                logger.info("✓ 强制更新成功")
                return True
            else:
                logger.error("✗ 强制更新失败")
                return False
        else:
            # 游戏不存在 -> 新增
            logger.info(f"游戏不存在，新增到 Notion: {game_name}")
            if add_game_to_notion(game, achievements_info, steam_store_data):
                logger.info("✓ 新增成功")
                return True
            else:
                logger.error("✗ 新增失败")
                return False
    
    except Exception as e:
        logger.error(f"处理游戏失败: {e}")
        return False


def add_multiple_games_by_appids(appids_str):
    """通过多个 appid 添加或更新游戏（支持逗号分隔）"""
    # 解析 appid 列表
    try:
        appids = [int(aid.strip()) for aid in appids_str.split(',')]
    except ValueError as e:
        logger.error(f"✗ AppID 格式错误: {e}")
        logger.info("用法: python notion_game_list.py add 387290,24534,5501")
        return False
    
    logger.info(f"开始处理 {len(appids)} 个游戏")
    success_count = 0
    
    for idx, appid in enumerate(appids, 1):
        logger.info(f"\n[{idx}/{len(appids)}] 处理 AppID: {appid}")
        if add_single_game_by_appid(appid):
            success_count += 1
        time.sleep(0.5)  # API 限制
    
    logger.info("\n" + "=" * 50)
    logger.info(f"处理完成! 成功: {success_count}/{len(appids)}")
    logger.info("=" * 50)
    return success_count == len(appids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steam 游戏同步到 Notion")
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    # 添加子命令或位置参数支持 add appid 的方式
    parser.add_argument('action', nargs='?', default='sync', help='执行的操作: sync (同步所有) 或 add')
    parser.add_argument('appid', nargs='?', type=str, help='游戏的 AppID (可用逗号分隔多个)')
    
    args = parser.parse_args()
    
    # 配置日志
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 添加处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(console_handler)
    
    if args.debug:
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
        logger.addHandler(file_handler)
    
    # 根据不同的操作执行相应的函数
    if args.action.lower() == 'add':
        if args.appid is None:
            logger.error("错误: 使用 'add' 命令时必须提供 appid")
            logger.info("用法: python notion_game_list.py add <appid>")
            logger.info("      python notion_game_list.py add 387290,24534,5501")
            exit(1)
        
        # 检查是否包含逗号（多个 appid）
        if ',' in args.appid:
            add_multiple_games_by_appids(args.appid)
        else:
            # 单个 appid
            add_single_game_by_appid(int(args.appid))
    elif args.action.lower() == 'sync':
        main()
    else:
        logger.error(f"未知的操作: {args.action}")
        logger.info("可用操作: sync (默认), add <appid>")
        exit(1)