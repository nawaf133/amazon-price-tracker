<div align="center">

# 🛒 Amazon Price Tracker

**A Python bot that watches Amazon prices and pings you on Discord and Telegram the moment a product hits your target price.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-7C3AED?style=for-the-badge&logo=render&logoColor=white)](https://YOUR-APP.onrender.com)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

<img src="docs/demo.gif" alt="demo" width="780" />

</div>

## ✨ Features

- Tracks any number of Amazon products (`amazon.sa`, `.com`, `.ae`, ...) from a simple `products.json`
- Sends alerts to **Discord** (rich embed) and **Telegram** at the same time
- Stores full price history in SQLite
- Web dashboard with a price chart for every product
- Smart alerts: only notifies when the price drops to your target, not on every check
- Polite scraping: random delays, captcha detection, one failing channel never blocks the other

## 🚀 Quick start

```bash
git clone https://github.com/nawaf133/amazon-price-tracker.git
cd amazon-price-tracker
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then fill it in
```

1. Edit `products.json` with your products and target prices:

```json
[{ "name": "My headphones", "url": "https://www.amazon.sa/dp/B0XXXXXXXX", "target_price": 250 }]
```

2. Run it:

```bash
python tracker.py          # check once
python tracker.py --loop   # check every CHECK_INTERVAL_HOURS
python app.py              # dashboard at http://localhost:5000
```

## 🔔 Setting up notifications

**Discord**: Server Settings → Integrations → Webhooks → New Webhook → Copy URL → `DISCORD_WEBHOOK_URL`

**Telegram**: talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token → `TELEGRAM_BOT_TOKEN`. Send your bot a message, then get your id from [@userinfobot](https://t.me/userinfobot) → `TELEGRAM_CHAT_ID`

## ☁️ Deploy the dashboard on Render

1. Push this repo to GitHub
2. On [render.com](https://render.com): **New → Blueprint** → pick this repo (it reads `render.yaml`)
3. The public demo runs with `DEMO_MODE=1` (sample data, no scraping). Copy the URL into the badge at the top of this README.

> The free Render plan sleeps after inactivity, so the first load can take ~30 seconds.

To run real tracking 24/7, deploy the same repo on a VPS or a Raspberry Pi and run `python tracker.py --loop`, or set `ENABLE_TRACKER=1` on an always-on host.

## 🗂 Project structure

```
├── tracker.py      # scraper + alerts (Discord / Telegram)
├── app.py          # Flask dashboard + JSON API
├── db.py           # SQLite price history
├── products.json   # what to track
├── render.yaml     # one-click Render deploy
└── .env.example
```

## ⚠️ Notes

Scraping Amazon pages may go against their Terms of Service and Amazon can show a captcha or change its HTML at any time. Keep the interval reasonable (3h+) and use this for personal purposes. For production use, prefer the official Amazon Product Advertising API.

## 📄 License

MIT
