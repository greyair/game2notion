# -*- coding: utf-8 -*-
"""
配置文件 - 管理 Notion 属性名和环境变量
"""

import os
#from dotenv import load_dotenv

#load_dotenv()

# ==================== STEAM 配置 ====================
STEAM_API_KEY = os.environ.get("STEAM_API_KEY") or '***REMOVED***'
STEAM_USER_ID = os.environ.get("STEAM_USER_ID") or '***REMOVED***'

# ==================== NOTION 配置 ====================
NOTION_API_KEY = os.environ.get("NOTION_API_KEY") or '***REMOVED***'
NOTION_GAMES_DATABASE_ID = os.environ.get("NOTION_GAMES_DATABASE_ID") or '***REMOVED***'
NOTION_DAILY_RECORDS_DB_ID = os.environ.get("NOTION_DAILY_RECORDS_DB_ID")

# ==================== NOTION 属性名映射 ====================
# 游戏库属性
NOTION_PROPERTIES = {
    "name": "游戏名称",                   # 游戏名称（title）
    "game_name": "游戏商品名",            # 游戏商品名（rich_text）
    "playtime": "游戏时长",               # 游玩时间（number，小时）
    "genres": "游戏类型",                 # 游戏类型（multi_select）
    "developers": "开发商",               # 开发商（multi_select）
    "publishers": "发行商",               # 发行商（multi_select）
    "release_date": "发行日期",           # 发行日期（date）
    "last_play": "上次游玩时间",          # 上次游玩时间（date）
    "store_url": "商店链接",              # 商店链接（url）
    "total_achievements": "成就总数",     # 成就总数（number）
    "achieved_achievements": "获得成就",  # 获得成就（number）
    "earliest_unlock": "成就首次解锁",    # 成就首次解锁（date）
    "info": "游戏简介",                   # 游戏简介（rich_text）
    "tags": "游戏标签",                   # 游戏标签（multi_select）
    "platform": "游戏平台",               # 游戏平台（select）
    "price": "商店价格",                  # 商店价格（rich_text）
    "review": "玩家评分",                 # 玩家评分（select）
    "appid": "appid"                      # appid（rich_text）
}

# 每日记录属性
NOTION_DAILY_PROPERTIES = {
    "date": "日期",                      # 日期（date）
    "title": "标题",                     # 标题（title）
    "game_name": "游戏名称",             # 游戏名称（relation）
    "playtime": "游玩时间",              # 当日游玩时间（number）
    "playtime_forever": "总游玩时间"     # 累计游玩时间（number）
}

# ==================== 业务配置 ====================
include_played_free_games = os.environ.get("include_played_free_games", "true").lower() == "true"
enable_item_update = os.environ.get("enable_item_update", "true").lower() == "true"
enable_filter = os.environ.get("enable_filter", "false").lower() == "true"

MAX_RETRIES = 3
RETRY_DELAY = 1

# ==================== 辅助函数 ====================
def get_property_name(prop_key, is_daily=False):
    """获取属性的实际名称"""
    props = NOTION_DAILY_PROPERTIES if is_daily else NOTION_PROPERTIES
    return props.get(prop_key, prop_key)