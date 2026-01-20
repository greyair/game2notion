# -*- coding: utf-8 -*-
"""
游戏平台模块 - 各平台API接口
"""

from .steam import (
    get_owned_games_from_steam,
    get_steam_recent_games,
    get_achievements_from_steam,
    parse_achievements_info,
    get_steam_store_info
)

__all__ = [
    'get_owned_games_from_steam',
    'get_steam_recent_games',
    'get_achievements_from_steam',
    'parse_achievements_info',
    'get_steam_store_info'
]
