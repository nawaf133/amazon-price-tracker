"""Web dashboard (deploy on Render). Optionally runs the tracker in the background."""
import os
import random
import threading
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string

load_dotenv()

import db  # noqa: E402

app = Flask(__name__)
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"


def seed_demo():
    """Fake 30-day history so the public demo is never empty."""
    with db.conn() as c:
        if c.execute("SELECT COUNT(*) FROM prices").fetchone()[0]:
            return
    items = [("Demo: Wireless Headphones", 349.0), ("Demo: Mechanical Keyboard", 259.0),
             ("Demo: 4K Monitor", 1099.0)]
    now = datetime.now(timezone.utc)
    rnd = random.Random(7)
    for i, (name, base) in enumerate(items):
        price = base
        for d in range(30, -1, -1):
            price = max(base * 0.7, min(base * 1.1, price + rnd.uniform(-base * 0.04, base * 0.03)))
            ts = (now - timedelta(days=d, hours=i)).isoformat(timespec="seconds")
            db.add_price(f"https://example.com/demo-{i}", name, round(price, 2), ts)


def start_tracker():
    import tracker
    threading.Thread(target=tracker.run_loop, daemon=True).start()


if DEMO_MODE:
    seed_demo()
if os.getenv("ENABLE_TRACKER", "0") == "1":
    start_tracker()


@app.get("/api/data")
def data():
    return jsonify(db.history())


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Amazon Price Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
 :root{--bg:#0d1117;--card:#161b22;--tx:#e6edf3;--mut:#8b949e;--ac:#a78bfa;--ok:#34d399}
 *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--tx);font-family:system-ui,sans-serif}
 header{padding:32px 20px 8px;text-align:center}
 h1{margin:0;font-size:28px;background:linear-gradient(90deg,#7c3aed,#06b6d4);-webkit-background-clip:text;color:transparent}
 p.sub{color:var(--mut);margin:6px 0 0}
 .badge{display:inline-block;margin-top:10px;padding:3px 10px;border-radius:99px;background:#7c3aed33;color:var(--ac);font-size:12px}
 main{max-width:1000px;margin:24px auto;padding:0 16px;display:grid;gap:16px}
 .card{background:var(--card);border:1px solid #30363d;border-radius:14px;padding:18px}
 .top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline}
 .name{font-weight:600} .price{font-size:26px;font-weight:700;color:var(--ok)}
 .stats{color:var(--mut);font-size:13px;margin:4px 0 12px}
 .empty{text-align:center;color:var(--mut)}
</style></head><body>
<header><h1>Amazon Price Tracker</h1>
<p class="sub">Python bot that watches prices and alerts Discord + Telegram</p>
{% if demo %}<span class="badge">Demo data</span>{% endif %}</header>
<main id="root"><div class="card empty">Loading...</div></main>
<script>
fetch('/api/data').then(r=>r.json()).then(d=>{
  const root=document.getElementById('root'); root.innerHTML='';
  const urls=Object.keys(d);
  if(!urls.length){root.innerHTML='<div class="card empty">No data yet. Run the tracker first.</div>';return;}
  urls.forEach((u,i)=>{
    const it=d[u], ps=it.points.map(x=>x.p);
    const cur=ps[ps.length-1], lo=Math.min(...ps), hi=Math.max(...ps);
    const el=document.createElement('div'); el.className='card';
    el.innerHTML=`<div class="top"><span class="name">${it.name||u}</span><span class="price">${cur.toFixed(2)}</span></div>
      <div class="stats">Lowest ${lo.toFixed(2)} &middot; Highest ${hi.toFixed(2)} &middot; ${ps.length} checks</div>
      <canvas id="c${i}" height="90"></canvas>`;
    root.appendChild(el);
    new Chart(document.getElementById('c'+i),{type:'line',
      data:{labels:it.points.map(x=>x.t.slice(5,16).replace('T',' ')),
            datasets:[{data:ps,borderColor:'#a78bfa',backgroundColor:'#a78bfa22',fill:true,tension:.3,pointRadius:0}]},
      options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#8b949e',maxTicksLimit:6},grid:{display:false}},
               y:{ticks:{color:'#8b949e'},grid:{color:'#30363d'}}}}});
  });
});
</script></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE, demo=DEMO_MODE)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
