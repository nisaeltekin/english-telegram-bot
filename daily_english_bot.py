import requests
import json
import os
from datetime import datetime, timedelta
import pytz
import time
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = "8337814716:AAFIXjzLAySvCpwGg4zYHQ-1N5hltynaLkA"
CHAT_ID = "1588882211"
tz = pytz.timezone("Europe/Istanbul")
DATA_FILE = "data.json"

def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def today():
    return datetime.now(tz).strftime("%Y-%m-%d")

def yesterday():
    return (datetime.now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")

def daily_tasks():
    data = load()
    t = today()
    data[t] = {"1": False, "2": False, "3": False}
    save(data)
    send("📚 Günlük İngilizce Görevlerin:\n\n"
         "Görev 1 - 🎧 Dinleme:\nBBC Learning English'ten bir video izle.\nhttps://www.bbc.co.uk/learningenglish\nBitince: yaptım1\n\n"
         "Görev 2 - ✍️ Yazma:\n5-6 İngilizce cümle yaz, Notepad'e kaydet.\nBitince: yaptım2\n\n"
         "Görev 3 - 🗣️ Konuşma/Kelime:\n10 yeni kelime öğren ve sesli tekrar et.\nhttps://www.vocabulary.com\nBitince: yaptım3")

def remind():
    data = load()
    t = today()
    if t not in data:
        return
    incomplete = [k for k, v in data[t].items() if not v]
    if incomplete:
        tasks = {"1": "Dinleme 🎧", "2": "Yazma ✍️", "3": "Konuşma/Kelime 🗣️"}
        msg = "⏰ Henüz tamamlamadığın görevler:\n"
        for k in incomplete:
            msg += f"- {tasks[k]} → yaptım{k}\n"
        send(msg)

def prev_day_remind():
    data = load()
    y = yesterday()
    if y not in data:
        return
    incomplete = [k for k, v in data[y].items() if not v]
    if incomplete:
        tasks = {"1": "Dinleme 🎧", "2": "Yazma ✍️", "3": "Konuşma/Kelime 🗣️"}
        msg = "⚠️ Dünkü tamamlanmayan görevler:\n"
        for k in incomplete:
            msg += f"- {tasks[k]}\n"
        send(msg)

def weekly_summary():
    data = load()
    now = datetime.now(tz)
    week = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    total, done = 0, 0
    for d in week:
        if d in data:
            total += 3
            done += sum(1 for v in data[d].values() if v)
    send(f"📊 Haftalık Özet:\n{done}/{total} görev tamamlandı ✅")

def listen():
    offset = None
    while True:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        try:
            r = requests.get(url, params=params, timeout=35)
            updates = r.json().get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message", {}).get("text", "").strip().lower()
                data = load()
                t = today()
                if t not in data:
                    data[t] = {"1": False, "2": False, "3": False}
                tasks = {"yaptım1": "1", "yaptım2": "2", "yaptım3": "3"}
                names = {"1": "Dinleme 🎧", "2": "Yazma ✍️", "3": "Konuşma/Kelime 🗣️"}
                if msg in tasks:
                    k = tasks[msg]
                    data[t][k] = True
                    save(data)
                    send(f"✅ {names[k]} tamamlandı! Harika iş!")
        except:
            pass
        time.sleep(1)

scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(daily_tasks, 'cron', hour=17, minute=0)
scheduler.add_job(remind, 'interval', hours=1)
scheduler.add_job(prev_day_remind, 'cron', hour=9, minute=0)
scheduler.add_job(weekly_summary, 'cron', day_of_week='sun', hour=18, minute=0)
scheduler.start()

send("✅ Bot başlatıldı! Her gün 17:00'de görevlerin gelecek.")
listen()
```
