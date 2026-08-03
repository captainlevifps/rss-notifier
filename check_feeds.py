#!/usr/bin/env python3
"""
RSS -> Discord Webhook notifier.
بيقرا config.yaml, يجيب كل feed, يقارنها بالـ seen.json,
ويبعت اللي جديد بس على الـ webhook بتاع القناة، مع mention لو متظبط.
"""

import json
import os
import time
from pathlib import Path

import feedparser
import requests
import yaml

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
SEEN_PATH = BASE_DIR / "seen.json"
MAX_SEEN_PER_FEED = 300          # عدد الـ ids المحفوظة لكل feed (عشان الملف متكبرش)
MAX_NEW_PER_RUN = 8              # حماية: منبعتش أكتر من كذا رسالة دفعة واحدة لو الفيد اتفتح جديد
SLEEP_BETWEEN_POSTS = 1.5        # ثواني بين كل رسالة عشان مانضربش rate limit بتاع Discord


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_seen():
    if SEEN_PATH.exists():
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def resolve_value(value):
    """
    بيسمح تحط في config.yaml قيمة زي: "$F1_WEBHOOK"
    عشان تتقرا من environment variable (GitHub Secrets) بدل ما تتكتب صريح في الملف.
    """
    if isinstance(value, str) and value.startswith("$"):
        return os.environ.get(value[1:], "")
    return value or ""


def entry_id(entry):
    return entry.get("id") or entry.get("link") or entry.get("title", "")


def entry_image(entry):
    """يحاول يلاقي صورة للخبر من أشكال مختلفة بتتبعت في الـ RSS."""
    media = entry.get("media_thumbnail") or entry.get("media_content")
    if media:
        url = media[0].get("url")
        if url:
            return url
    for l in entry.get("links", []):
        if str(l.get("type", "")).startswith("image/"):
            return l.get("href")
    if entry.get("summary"):
        import re
        m = re.search(r'<img[^>]+src="([^"]+)"', entry["summary"])
        if m:
            return m.group(1)
    return None


def clean_summary(entry, max_len=200):
    summary = entry.get("summary", "")
    if not summary:
        return ""
    import re
    text = re.sub(r"<[^>]+>", "", summary).strip()
    return (text[:max_len] + "…") if len(text) > max_len else text


def post_to_discord(webhook_url, payload):
    resp = requests.post(webhook_url, json=payload, timeout=15)
    if resp.status_code >= 300:
        print(f"  [!] Discord error {resp.status_code}: {resp.text[:200]}")
    return resp.status_code < 300


def process_feed(feed_cfg, seen):
    name = feed_cfg["name"]
    url = resolve_value(feed_cfg["url"])
    webhook = resolve_value(feed_cfg.get("webhook"))
    mention = resolve_value(feed_cfg.get("mention", ""))
    label = feed_cfg.get("label", name)                 # اسم المصدر اللي هيظهر فوق الـ embed
    color = int(feed_cfg.get("color", "0x5865F2"), 16) if isinstance(feed_cfg.get("color"), str) else feed_cfg.get("color", 0x5865F2)
    keywords = [k.lower() for k in feed_cfg.get("keywords", [])]  # لو عايز تفلتر بكلمات معينة (اختياري)

    if not webhook:
        print(f"[{name}] webhook not set, skipping")
        return

    print(f"[{name}] checking {url}")
    parsed = feedparser.parse(url)
    if parsed.bozo and not parsed.entries:
        print(f"  [!] couldn't parse feed: {parsed.bozo_exception}")
        return

    seen_ids = set(seen.get(name, []))
    # الفيد بيرجع الأحدث الأول، فبنقلبها عشان لو فيه أكتر من خبر جديد يتبعتوا بترتيب زمني صح
    new_entries = []
    for entry in parsed.entries:
        eid = entry_id(entry)
        if eid and eid not in seen_ids:
            new_entries.append(entry)
    new_entries.reverse()

    if not new_entries:
        print("  no new items")
        return

    # أول مرة تشغل فيها الفيد: منبعتش كل الأرشيف، بس نسجله كـ "متشاف" عشان نبدأ نتابع من دلوقتي
    first_run = name not in seen
    if first_run:
        for entry in new_entries:
            seen_ids.add(entry_id(entry))
        seen[name] = list(seen_ids)[-MAX_SEEN_PER_FEED:]
        print(f"  first run: marking {len(new_entries)} existing items as seen (no messages sent)")
        return

    posted = 0
    for entry in new_entries:
        if posted >= MAX_NEW_PER_RUN:
            print(f"  [!] hit MAX_NEW_PER_RUN limit, rest will post next run")
            break

        title = entry.get("title", "بدون عنوان")
        link = entry.get("link", "")

        if keywords and not any(k in title.lower() for k in keywords):
            seen_ids.add(entry_id(entry))
            continue

        prefix = mention if mention else ""
        image = entry_image(entry)
        embed = {
            "title": title[:256],
            "url": link,
            "color": color,
            "author": {"name": label},
            "description": clean_summary(entry),
        }
        if image:
            embed["image"] = {"url": image}

        payload = {"content": prefix, "embeds": [embed]}

        if post_to_discord(webhook, payload):
            print(f"  -> posted: {title}")
            posted += 1
            seen_ids.add(entry_id(entry))
            time.sleep(SLEEP_BETWEEN_POSTS)

    seen[name] = list(seen_ids)[-MAX_SEEN_PER_FEED:]


def main():
    config = load_config()
    seen = load_seen()

    for feed_cfg in config.get("feeds", []):
        try:
            process_feed(feed_cfg, seen)
        except Exception as e:
            print(f"[{feed_cfg.get('name')}] [!] error: {e}")

    save_seen(seen)


if __name__ == "__main__":
    main()
