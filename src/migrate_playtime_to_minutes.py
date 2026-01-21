# -*- coding: utf-8 -*-
"""
将 Notion 中的游玩时间从“小时”迁移为“分钟”。
运行一次即可，默认会同时迁移游戏库与每日记录库。

用法:
  python migrate_playtime_to_minutes.py
  python migrate_playtime_to_minutes.py --dry-run
  python migrate_playtime_to_minutes.py --skip-daily
"""

import argparse
import time
from config import (
    NOTION_API_KEY,
    NOTION_GAMES_DATABASE_ID,
    NOTION_DAILY_RECORDS_DB_ID,
    get_property_name,
)
from utils import get_logger, send_request_with_retry, setup_logging

logger = get_logger(__name__)


def _build_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _query_all_pages(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = _build_headers()

    has_more = True
    next_cursor = None

    while has_more:
        data = {"page_size": 100}
        if next_cursor:
            data["start_cursor"] = next_cursor

        response = send_request_with_retry(url, headers=headers, json_data=data, method="post")
        result = response.json()
        for page in result.get("results", []):
            yield page

        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")


def _update_page(page_id, properties, dry_run=False):
    if dry_run:
        logger.info(f"[DRY-RUN] update page {page_id}: {properties}")
        return

    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = _build_headers()
    send_request_with_retry(url, headers=headers, json_data={"properties": properties}, method="patch")


def migrate_games_playtime(dry_run=False):
    if not NOTION_GAMES_DATABASE_ID:
        logger.warning("未配置 NOTION_GAMES_DATABASE_ID，跳过游戏库迁移")
        return

    playtime_prop = get_property_name("playtime")
    updated = 0

    for page in _query_all_pages(NOTION_GAMES_DATABASE_ID):
        props = page.get("properties", {})
        playtime_hours = props.get(playtime_prop, {}).get("number")
        if playtime_hours is None or playtime_hours == 0:
            continue

        playtime_minutes = int(round(playtime_hours * 60))
        _update_page(page["id"], {
            playtime_prop: {"type": "number", "number": playtime_minutes}
        }, dry_run=dry_run)
        updated += 1
        time.sleep(0.2)

    logger.info(f"游戏库迁移完成，共更新 {updated} 条")


def migrate_daily_records_playtime(dry_run=False):
    if not NOTION_DAILY_RECORDS_DB_ID:
        logger.warning("未配置 NOTION_DAILY_RECORDS_DB_ID，跳过每日记录迁移")
        return

    playtime_prop = get_property_name("playtime", is_daily=True)
    total_prop = get_property_name("playtime_forever", is_daily=True)
    updated = 0

    for page in _query_all_pages(NOTION_DAILY_RECORDS_DB_ID):
        props = page.get("properties", {})
        playtime_hours = props.get(playtime_prop, {}).get("number")
        total_hours = props.get(total_prop, {}).get("number")

        if (playtime_hours is None or playtime_hours == 0) and (total_hours is None or total_hours == 0):
            continue

        update_props = {}
        if playtime_hours not in (None, 0):
            update_props[playtime_prop] = {"type": "number", "number": int(round(playtime_hours * 60))}
        if total_hours not in (None, 0):
            update_props[total_prop] = {"type": "number", "number": int(round(total_hours * 60))}

        _update_page(page["id"], update_props, dry_run=dry_run)
        updated += 1
        time.sleep(0.2)

    logger.info(f"每日记录迁移完成，共更新 {updated} 条")


def main():
    parser = argparse.ArgumentParser(description="将 Notion 游玩时间从小时迁移到分钟")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要更新的数据，不执行写入")
    parser.add_argument("--skip-daily", action="store_true", help="跳过每日记录库迁移")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    migrate_games_playtime(dry_run=args.dry_run)
    if not args.skip_daily:
        migrate_daily_records_playtime(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
