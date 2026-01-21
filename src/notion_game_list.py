# -*- coding: utf-8 -*-
"""
Steam 游戏信息同步到 Notion
"""

import argparse
import time
from datetime import datetime
from .config import (
    STEAM_API_KEY, STEAM_USER_ID, NOTION_API_KEY, NOTION_GAMES_DATABASE_ID,
    NOTION_DAILY_RECORDS_DB_ID,
    include_played_free_games, enable_item_update, enable_filter, enable_full_update,
    TIMEZONE,
    get_property_name
)
from .platforms.steam import (
    get_owned_games_from_steam, get_achievements_from_steam, 
    parse_achievements_info, get_steam_store_info
)
from .utils import (
    format_timestamp,
    format_notion_multi_select,
    get_logger,
    parse_steam_date,
    send_request_with_retry,
    setup_logging,
)

logger = get_logger(__name__)


def build_game_properties(game, achievements_info, steam_store_data):
    """构建游戏属性数据 - 使用配置文件中的属性名和统一的处理方法"""
    playtime = int(game.get("playtime_forever", 0))
    
    # 处理时间戳为日期字符串（仅当有值时）
    last_played_time = format_timestamp(game.get("rtime_last_played"), TIMEZONE, date_only=False)
    earliest_unlock = achievements_info.get("earliest_unlock")
    earliest_unlock_time = format_timestamp(earliest_unlock, TIMEZONE, date_only=True)
    
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
    genres = format_notion_multi_select(steam_store_data.get("genres", []))
    if genres:
        props[get_property_name("genres")] = {
            "type": "multi_select",
            "multi_select": genres
        }
    
    developers = format_notion_multi_select(steam_store_data.get("developers", []))
    if developers:
        props[get_property_name("developers")] = {
            "type": "multi_select",
            "multi_select": developers
        }
    
    publishers = format_notion_multi_select(steam_store_data.get("publishers", []))
    if publishers:
        props[get_property_name("publishers")] = {
            "type": "multi_select",
            "multi_select": publishers
        }
    
    tags = format_notion_multi_select(steam_store_data.get("tag", []))
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


def build_update_properties(game, achievements_info, steam_store_data, full_update=False):
    """构建更新属性数据（默认仅更新核心字段）"""
    if full_update:
        return build_game_properties(game, achievements_info, steam_store_data)

    playtime = int(game.get("playtime_forever", 0))
    last_played_time = format_timestamp(game.get("rtime_last_played"), TIMEZONE, date_only=False)
    achieved_achievements = achievements_info.get("achieved", -1)
    review = steam_store_data.get("review", "")

    props = {
        get_property_name("playtime"): {
            "type": "number",
            "number": playtime
        },
        get_property_name("achieved_achievements"): {
            "type": "number",
            "number": achieved_achievements
        }
    }

    if last_played_time:
        props[get_property_name("last_play")] = {
            "type": "date",
            "date": {"start": last_played_time}
        }

    if review:
        props[get_property_name("review")] = {
            "type": "select",
            "select": {"name": review}
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
    playtime_prop = get_property_name("playtime")
    
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
                    
                    playtime = props.get(playtime_prop, {}).get("number", 0)

                    key = (game_name, platform)
                    games_map[key] = {
                        "page_id": page_id,
                        "last_play": last_play,
                        "playtime": playtime
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


def update_game_in_notion(page_id, game, achievements_info, steam_store_data, force_update=None):
    """更新游戏信息在 Notion"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    if force_update is None:
        force_update = enable_full_update

    properties = build_update_properties(game, achievements_info, steam_store_data, full_update=force_update)
    data = {"properties": properties}
    
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
    
    playtime = int(game.get("playtime_forever", 0))
    last_played = game.get("rtime_last_played", 0)
    
    # 无游玩时间且无成就 -> 不记录
    if playtime < 6 and achievements_info["total"] < 1:
        return False
    
    # 长时间未玩且游玩时间少于6小时且无成就 -> 不记录
    week_ago = int(time.time()) - 7 * 86400
    if last_played < week_ago and playtime < 360 and achievements_info["total"] < 1:
        return False
    
    return True


def _fetch_game_details(game):
    """获取成就与商店信息（仅在需要时调用）"""
    achievements_data = get_achievements_from_steam(game, STEAM_API_KEY, STEAM_USER_ID)
    achievements_info = parse_achievements_info(achievements_data)
    steam_store_data = get_steam_store_info(game["appid"])
    if steam_store_data.get("tag") == []:
        steam_store_data = get_steam_store_info(game["appid"], country="SG")
    return achievements_info, steam_store_data


def _create_daily_record(game_name, playtime_today_minutes, playtime_forever_minutes, page_id, record_date):
    """创建每日游玩记录"""
    url = "https://api.notion.com/v1/pages"
    record_date_str = record_date or datetime.now().date().isoformat()

    data = {
        "parent": {
            "type": "database_id",
            "database_id": NOTION_DAILY_RECORDS_DB_ID,
        },
        "icon": {
            "type": "emoji",
            "emoji": "✅"
        },
        "properties": {
            get_property_name("date", is_daily=True): {
                "type": "date",
                "date": {"start": record_date_str}
            },
            get_property_name("title", is_daily=True): {
                "type": "title",
                "title": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "date",
                            "date": {"start": record_date_str}
                        }
                    }
                ]
            },
            get_property_name("game_name", is_daily=True): {
                "type": "relation",
                "relation": [{"id": page_id}]
            },
            get_property_name("playtime", is_daily=True): {
                "type": "number",
                "number": playtime_today_minutes
            },
            get_property_name("playtime_forever", is_daily=True): {
                "type": "number",
                "number": playtime_forever_minutes
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    send_request_with_retry(url, headers=headers, json_data=data, method="post")
    logger.info(f"✓ 已记录每日游玩: {game_name} - {playtime_today_minutes}min (累计: {playtime_forever_minutes}min)")


# ==================== MAIN ====================
def sync_games_to_notion(sync_daily=False):
    """同步 Steam 游戏到 Notion"""
    logger.info("=" * 50)
    logger.info("开始同步 Steam 游戏到 Notion")
    logger.info("=" * 50)

    if sync_daily and not NOTION_DAILY_RECORDS_DB_ID:
        logger.warning("未配置 NOTION_DAILY_RECORDS_DB_ID，跳过每日记录同步")
        sync_daily = False
    
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
        
        # 在本地查找游戏
        game_key = (game_name, "Steam")
        notion_game = notion_games_map.get(game_key)
        
        if notion_game:
            # 游戏已存在 -> 更新
            if enable_item_update and (notion_game["last_play"] is not None):
                page_id = notion_game["page_id"]
                last_play = notion_game["last_play"]
                logger.info(f"⊘ 上次游玩: {last_play}")
                game_last_played = format_timestamp(game.get("rtime_last_played"), TIMEZONE, date_only=False)
                game_last_played_date = format_timestamp(game.get("rtime_last_played"), TIMEZONE, date_only=True)
                
                if last_play != game_last_played:
                    achievements_info, steam_store_data = _fetch_game_details(game)
                    if update_game_in_notion(page_id, game, achievements_info, steam_store_data):
                        updated_count += 1
                        if sync_daily and NOTION_DAILY_RECORDS_DB_ID:
                            previous_minutes = int(notion_game.get("playtime", 0) or 0)
                            current_minutes = int(game.get("playtime_forever", 0))
                            playtime_today_minutes = current_minutes - previous_minutes
                            if playtime_today_minutes > 0:
                                _create_daily_record(
                                    game_name,
                                    playtime_today_minutes,
                                    current_minutes,
                                    page_id,
                                    game_last_played_date,
                                )
                else:
                    logger.info(f"⊘ 游玩时间未变更，跳过更新: {game_name}")
                    skipped_count += 1
            else:
                logger.info(f"⊘ 跳过更新: {game_name}")
                skipped_count += 1
        else:
            # 游戏不存在 -> 新增
            achievements_info, steam_store_data = _fetch_game_details(game)
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
            if update_game_in_notion(page_id, game, achievements_info, steam_store_data, force_update=True):
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
    parser.add_argument('--daily', action='store_true', help='同步 Notion 每日游戏记录')
    
    # 添加子命令或位置参数支持 add appid 的方式
    parser.add_argument('action', nargs='?', default='sync', help='执行的操作: sync (同步所有) 或 add')
    parser.add_argument('appid', nargs='?', type=str, help='游戏的 AppID (可用逗号分隔多个)')
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(debug=args.debug, logfile="app.log" if args.debug else None)
    
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
        sync_games_to_notion(sync_daily=args.daily)
    else:
        logger.error(f"未知的操作: {args.action}")
        logger.info("可用操作: sync (默认), add <appid>")
        exit(1)