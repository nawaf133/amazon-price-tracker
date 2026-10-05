"""Amazon price tracker -> Discord + Telegram alerts.

Usage:
    python tracker.py            # check once
    python tracker.py --loop     # check forever (every CHECK_INTERVAL_HOURS)
"""
import argparse
import html
import json
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

import db  # noqa: E402  (after load_dotenv so DB_PATH is picked up)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "3"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept": "text/html,application/xhtml+xml",
}

PRICE_SELECTORS = [
    "#corePrice_feature_div span.a-offscreen",
    "span.a-price span.a-offscreen",
    "#priceblock_ourprice",
    "#priceblock_dealprice",
    ".a-price .a-offscreen",
]


class BlockedError(Exception):
    """Amazon served a captcha / robot check."""


def parse_price(text):
    """'SAR 1,234.56' -> 1234.56"""
    m = re.search(r"\d[\d,]*\.?\d*", text.replace("\u066b", ".").replace("\u066c", ","))
    if not m:
        raise ValueError(f"cannot parse price from {text!r}")
    return float(m.group(0).replace(",", ""))


def fetch_product(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    if "api-services-support@amazon" in r.text or "Type the characters you see" in r.text:
        raise BlockedError("Amazon returned a robot check")
    soup = BeautifulSoup(r.text, "html.parser")

    title_el = soup.select_one("#productTitle")
    name = title_el.get_text(strip=True) if title_el else None

    for sel in PRICE_SELECTORS:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return name, parse_price(el.get_text())
    raise ValueError("price element not found (page layout changed or item unavailable)")


def send_discord(name, url, price, target, prev):
    if not DISCORD_WEBHOOK:
        return
    fields = [{"name": "Now", "value": f"{price:,.2f}", "inline": True},
              {"name": "Target", "value": f"{target:,.2f}", "inline": True}]
    if prev is not None:
        fields.append({"name": "Before", "value": f"{prev:,.2f}", "inline": True})
    payload = {
        "username": "Price Tracker",
        "embeds": [{
            "title": f"Price drop: {name[:200]}",
            "url": url,
            "color": 0x7C3AED,
            "fields": fields,
        }],
    }
    requests.post(DISCORD_WEBHOOK, json=payload, timeout=15).raise_for_status()


def send_telegram(name, url, price, target, prev):
    if not (TG_TOKEN and TG_CHAT):
        return
    before = f"\nBefore: {prev:,.2f}" if prev is not None else ""
    text = (
        f"<b>Price drop!</b>\n{html.escape(name)}\n\n"
        f"Now: <b>{price:,.2f}</b> (target {target:,.2f}){before}\n"
        f'<a href="{html.escape(url)}">Open on Amazon</a>'
    )
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"},
        timeout=15,
    ).raise_for_status()


def notify(name, url, price, target, prev):
    for fn in (send_discord, send_telegram):
        try:
            fn(name, url, price, target, prev)
        except Exception as e:  # one channel failing must not block the other
            print(f"  ! {fn.__name__} failed: {e}")


def should_alert(price, target, prev):
    if price > target:
        return False
    return prev is None or prev > target or price < prev


def check_all(products):
    for p in products:
        url, target = p["url"], float(p["target_price"])
        try:
            name, price = fetch_product(url)
            name = name or p.get("name") or url
            prev = db.last_price(url)
            db.add_price(url, name, price)
            print(f"[ok] {name[:60]} -> {price:,.2f} (target {target:,.2f})")
            if should_alert(price, target, prev):
                notify(name, url, price, target, prev)
        except BlockedError as e:
            print(f"[blocked] {url}: {e}. Try again later / less often.")
        except Exception as e:
            print(f"[error] {url}: {e}")
        time.sleep(random.uniform(4, 9))  # be polite


def load_products(path="products.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_loop():
    while True:
        check_all(load_products())
        time.sleep(INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="run forever")
    args = ap.parse_args()
    if args.loop:
        run_loop()
    else:
        check_all(load_products())
