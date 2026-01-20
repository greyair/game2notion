# -*- coding: utf-8 -*-
"""
每日游戏记录同步脚本
获取 Steam 最近游玩记录，同步到 Notion 每日记录数据库
"""

import datetime
import time
from config import (
    STEAM_API_KEY, STEAM_USER_ID, NOTION_API_KEY,
    NOTION_GAMES_DATABASE_ID, NOTION_DAILY_RECORDS_DB_ID
)
from gameplatform.steam1 import get_steam_recent_games
from utils import send_request_with_retry

# ==================== 常量 ====================
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def _build_notion_headers():
    """构建 Notion API 请求头"""
    return NOTION_HEADERS


def _minutes_to_hours(minutes):
    """将分钟转换为小时（保留2位小数）"""
    return round(minutes / 60, 2)


def query_notion_games_page_id():
    """查询 Notion 游玩进度表，获取游戏名称与 page_id 的映射"""
    url = f"https://api.notion.com/v1/databases/{NOTION_GAMES_DATABASE_ID}/query"
    games_mapping = {}  # {game_name: page_id}
    has_more = True
    next_cursor = None
    
    while has_more:
        data = {"page_size": 100}
        if next_cursor:
            data["start_cursor"] = next_cursor
        
        try:
            response = send_request_with_retry(
                url, 
                headers=_build_notion_headers(), 
                json_data=data
            )
            result = response.json()
            
            for page in result["results"]:
                props = page.get("properties", {})
                try:
                    # 读取游戏名称（title）
                    game_name_prop = props.get("游戏名称", {}).get("title", [])
                    if game_name_prop:
                        game_name = game_name_prop[0]["plain_text"]
                        page_id = page.get("id")
                        games_mapping[game_name] = page_id
                except Exception as e:
                    print(f"解析游戏信息失败: {e}")
            
            has_more = result.get("has_more", False)
            next_cursor = result.get("next_cursor")
        
        except Exception as e:
            print(f"查询 Notion 失败: {e}")
            break
    
    print(f"[INFO] 获取 {len(games_mapping)} 个游戏的 page_id 映射")
    return games_mapping


def query_today_records():
    """查询今天已记录的游戏及其信息"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DAILY_RECORDS_DB_ID}/query"
    today = datetime.date.today().isoformat()
    data = {
        "filter": {
            "property": "日期",
            "date": {"equals": today}
        }
    }
    
    try:
        response = send_request_with_retry(
            url, 
            headers=_build_notion_headers(), 
            json_data=data
        )
        result = response.json()
        
        recorded_games = {}  # {page_id: total_playtime}
        for page in result["results"]:
            props = page.get("properties", {})
            game_name_prop = props.get("游戏名称", {}).get("relation", [])
            total_playtime = props.get("总游玩时间", {}).get("number", 0)
            
            if game_name_prop:
                page_id = game_name_prop[0]["id"]
                recorded_games[page_id] = total_playtime
        
        return recorded_games
    except Exception as e:
        print(f"查询今日记录失败: {e}")
        return {}


def query_last_game_record(page_id):
    """查询该游戏最后一条记录，获取上次的 playtime_forever 和记录日期"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DAILY_RECORDS_DB_ID}/query"
    data = {
        "filter": {
            "property": "游戏名称",
            "relation": {"contains": page_id}
        },
        "sorts": [{"property": "日期", "direction": "descending"}],
        "page_size": 1
    }
    
    try:
        response = send_request_with_retry(
            url, 
            headers=_build_notion_headers(), 
            json_data=data
        )
        result = response.json()
        
        if result["results"]:
            page = result["results"][0]
            props = page.get("properties", {})
            last_total_playtime = props.get("总游玩时间", {}).get("number", 0)
            last_date = props.get("日期", {}).get("date", {}).get("start")
            return last_total_playtime, last_date
        else:
            return None, None
    except Exception as e:
        print(f"查询上次记录失败: {e}")
        return None, None


def create_daily_record(game_name, playtime_today_hours, playtime_forever, page_id):
    """创建每日游玩记录"""
    url = "https://api.notion.com/v1/pages"
    today = datetime.date.today().isoformat()
    playtime_forever_hours = _minutes_to_hours(playtime_forever)
    
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
            "日期": {
                "type": "date",
                "date": {"start": today}
            },
            "标题": {
                "type": "title",
                "title": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "date",
                            "date": {"start": today}
                        }
                    }
                ]
            },
            "游戏名称": {
                "type": "relation",
                "relation": [{"id": page_id}]
            },
            "游玩时间": {
                "type": "number",
                "number": playtime_today_hours
            },
            "总游玩时间": {
                "type": "number",
                "number": playtime_forever_hours
            }
        }
    }
    
    try:
        send_request_with_retry(
            url, 
            headers=_build_notion_headers(), 
            json_data=data
        )
        print(f"✓ 已记录: {game_name} - {playtime_today_hours}h (累计: {playtime_forever_hours}h)")
        return True
    except Exception as e:
        print(f"✗ 记录失败 {game_name}: {e}")
        return False


def sync_daily_records():
    """同步每日游玩记录"""
    print("[INFO] 开始同步每日游玩记录...")
    
    # 1. 获取所有游戏（包含 playtime_forever）
    all_games = get_steam_recent_games(STEAM_API_KEY, STEAM_USER_ID)
    if not all_games:
        print("未获取到 Steam 游戏数据")
        return
    
    # 2. 获取所有游戏的 page_id 映射
    games_mapping = query_notion_games_page_id()
    if not games_mapping:
        print("未获取到 Notion 游戏数据")
        return
    
    # 3. 查询今天已记录的游戏
    recorded_games = query_today_records()  # {page_id: total_playtime}
    today = datetime.date.today().isoformat()
    
    # 4. 处理每个游戏
    count = 0
    for game in all_games:
        game_name = game.get("name")
        playtime_forever = game.get("playtime_forever", 0)  # 总游玩时间（分钟）
        playtime_forever_hours = _minutes_to_hours(playtime_forever)
        
        # 跳过不在 Notion 游戏表中的游戏
        if game_name not in games_mapping:
            continue
        
        page_id = games_mapping[game_name]
        
        # 检查今天是否已记录过此游戏
        if page_id in recorded_games:
            recorded_total = recorded_games[page_id]
            if playtime_forever_hours == recorded_total:
                print(f"⊘ 跳过: {game_name} (今天已记录，时间无变化)")
            else:
                print(f"⊘ 跳过: {game_name} (今天已记录，总时间变化: {recorded_total}h → {playtime_forever_hours}h)")
            continue
        
        # 查询该游戏的上次记录
        last_total_playtime, last_date = query_last_game_record(page_id)
        
        # 跳过重复记录（同一天的记录已存在）
        if last_date == today:
            print(f"⊘ 跳过: {game_name} (今天已有记录)")
            continue
        
        # 计算当日游玩时间
        if last_total_playtime is not None:
            # 有历史记录：用差值计算当日游玩时间
            playtime_today_hours = round(playtime_forever_hours - last_total_playtime, 2)
            
            # 检查差值是否合理（防止数据错误）
            if playtime_today_hours <= 0:
                print(f"⊘ 跳过: {game_name} (无新游玩时间或数据不一致)")
                continue
        else:
            # 无历史记录：首次记录，直接使用 playtime_forever
            playtime_today_hours = playtime_forever_hours
            
            if playtime_today_hours == 0:
                print(f"⊘ 跳过: {game_name} (无游玩时间)")
                continue
        
        # 创建记录
        if create_daily_record(game_name, playtime_today_hours, playtime_forever, page_id):
            count += 1
        
        time.sleep(0.3)
    
    print(f"[INFO] 本次同步新增 {count} 条记录")


def main():
    """主函数"""
    try:
        sync_daily_records()
        print("[INFO] 同步完成！")
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")


if __name__ == "__main__":
    main()
