# -*- coding: utf-8 -*-
"""
从 CSV 导入购买信息到 Notion 游戏库。
CSV 格式：
- 第 1 列：日期
- 第 2 列：游戏名
- 第 3 列：购买方式
"""

import argparse
import csv
import difflib
from config import NOTION_API_KEY, NOTION_GAMES_DATABASE_ID, get_property_name
from utils import get_logger, parse_steam_date, send_request_with_retry, setup_logging

logger = get_logger(__name__)


def _build_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _query_steam_games():
    """一次性获取 Notion 游戏库中平台为 Steam 的条目"""
    url = f"https://api.notion.com/v1/databases/{NOTION_GAMES_DATABASE_ID}/query"
    headers = _build_headers()

    name_prop = get_property_name("name")
    game_name_prop = get_property_name("game_name")
    platform_prop = get_property_name("platform")

    has_more = True
    next_cursor = None
    games = []

    while has_more:
        data = {
            "page_size": 100,
            "filter": {
                "property": platform_prop,
                "select": {"equals": "Steam"}
            }
        }
        if next_cursor:
            data["start_cursor"] = next_cursor

        response = send_request_with_retry(url, headers=headers, json_data=data, method="post")
        result = response.json()

        games.extend(result.get("results", []))
        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")

    games_map = {}
    for page in games:
        props = page.get("properties", {})
        title_data = props.get(name_prop, {}).get("title", [])
        game_name_data = props.get(game_name_prop, {}).get("rich_text", [])

        name = title_data[0].get("plain_text") if title_data else ""
        game_name = game_name_data[0].get("plain_text") if game_name_data else ""

        if name:
            games_map[name.strip().lower()] = (page["id"], name.strip())
        if game_name:
            games_map[game_name.strip().lower()] = (page["id"], game_name.strip())

    logger.info(f"✓ 获取 Steam 游戏条目 {len(games_map)} 个")
    return games_map


def _normalize_name(value):
    if not value:
        return ""
    base = value.split("-", 1)[0].strip() if "-" in value else value.strip()
    base = base.replace("CN", "").replace("cn", "").strip()
    return base.lower()


def _name_variants(value):
    if not value:
        return []
    variants = []
    normalized = _normalize_name(value)
    if normalized:
        variants.append(normalized)
    if ":" in value:
        left = value.split(":", 1)[0].strip()
        left_norm = _normalize_name(left)
        if left_norm and left_norm not in variants:
            variants.append(left_norm)
    return variants


def _find_best_match(name, games_map, cutoff=0.75):
    if not name:
        return None

    if name in games_map:
        return games_map[name]

    best_key = None
    best_score = 0.0
    for key in games_map.keys():
        score = difflib.SequenceMatcher(None, name, key).ratio()
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score >= cutoff:
        return games_map[best_key]
    return None


def _update_game_page(page_id, activation_date, purchase_channel, dry_run=False):
    """更新游戏条目购买信息"""
    activation_prop = get_property_name("activation_time")
    purchase_channel_prop = get_property_name("purchase_channel")
    purchase_time_prop = get_property_name("purchase_time")

    normalized_date = None
    if activation_date:
        parsed_date = parse_steam_date(activation_date)
        normalized_date = parsed_date.isoformat() if parsed_date else activation_date

    properties = {}

    if normalized_date:
        properties[activation_prop] = {
            "type": "date",
            "date": {"start": normalized_date}
        }

    if purchase_channel in {"steam商店", "免费赠送", "Steam 商店"}:
        properties[purchase_channel_prop] = {
            "type": "select",
            "select": {"name": purchase_channel}
        }

        if purchase_channel == "Steam 商店" and normalized_date:
            properties[purchase_time_prop] = {
                "type": "date",
                "date": {"start": normalized_date}
            }

    if not properties:
        return False

    if dry_run or purchase_channel != "Steam 商店":
        logger.info(f"[DRY-RUN] update page {page_id}: {properties}")
        return True

    url = f"https://api.notion.com/v1/pages/{page_id}"
    send_request_with_retry(url, headers=_build_headers(), json_data={"properties": properties}, method="patch")
    return True


def import_csv(csv_path, dry_run=False, output_missing=None):
    if not NOTION_GAMES_DATABASE_ID:
        logger.error("未配置 NOTION_GAMES_DATABASE_ID")
        return

    games_map = _query_steam_games()

    updated = 0
    skipped = 0
    missing_rows = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader, 1):
            if len(row) < 3:
                logger.info(f"⊘ 第 {idx} 行列数不足，跳过")
                skipped += 1
                continue

            date_val = row[0].strip()
            name_val = row[1].strip()
            channel_val = row[2].strip()

            if not name_val:
                skipped += 1
                continue

            page_id = None
            matched_name = None
            for candidate in _name_variants(name_val):
                match = _find_best_match(candidate, games_map)
                if match:
                    page_id, matched_name = match
                    break
            if not page_id:
                logger.info(f"⊘ 未找到游戏，跳过: {name_val}")
                missing_rows.append([date_val, name_val, channel_val])
                skipped += 1
                continue

            logger.info(f"✓ 匹配成功: CSV=\"{name_val}\" -> Notion=\"{matched_name}\"")

            if _update_game_page(page_id, date_val, channel_val, dry_run=dry_run):
                updated += 1
            else:
                skipped += 1

    logger.info(f"导入完成：更新 {updated} 条，跳过 {skipped} 条")

    if output_missing and missing_rows:
        with open(output_missing, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(missing_rows)
        logger.info(f"未匹配游戏已输出: {output_missing}")


def main():
    parser = argparse.ArgumentParser(description="导入 CSV 到 Notion 游戏库")
    parser.add_argument("csv", help="CSV 文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要更新的数据，不执行写入")
    parser.add_argument("--output-missing", help="输出未匹配游戏的 CSV 文件路径")
    args = parser.parse_args()

    setup_logging(debug=args.debug, logfile="app.log" if args.debug else None)
    import_csv(args.csv, dry_run=args.dry_run, output_missing=args.output_missing)


if __name__ == "__main__":
    main()
