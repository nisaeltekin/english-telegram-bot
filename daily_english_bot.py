from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
import json
import os

# ------------------ Kullanıcı Ayarları ------------------
TOKEN = "8337814716:AAFIXjzLAySvCpwGg4zYHQ-1N5hltynaLkA"      
CHAT_ID = 1588882211  
tz = pytz.timezone("Europe/Istanbul")  # Türkiye saati
DATA_FILE = "english_bot_data.json"

bot = Bot(token=TOKEN)
scheduler = BackgroundScheduler(timezone=tz)

# ------------------ Veri Dosyası ------------------
# Eğer yoksa oluştur
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# ------------------ Yardımcı Fonksiyonlar ------------------
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_today_key():
    return datetime.now(tz).strftime("%Y-%m-%d")

def send_message(text):
    bot.send_message(chat_id=CHAT_ID, text=text)

# ------------------ Görevler ve Kaynaklar ------------------
daily_tasks = [
    {"id": 1, "name": "Dinleme", "source": "BBC Learning English / VOA / YouTube kısa videolar"},
    {"id": 2, "name": "Yazma", "source": "Günlük 5-6 cümle → Google Docs veya Notepad"},
    {"id": 3, "name": "Konuşma / Kelime", "source": "Ses kaydı → 10 yeni kelime tekrar et"}
]

extra_tasks = [
    {"id": 4, "name": "Okuma / Grammar", "source": "English Grammar in Use / Breaking News English"}
]

# ------------------ Günlük Görev Mesajı ------------------
def send_daily_tasks():
    data = load_data()
    today = get_today_key()

    if today not in data:
        data[today] = {"tasks": {}, "completed": {}}

    msg = f"🌞 Günlük İngilizce Görevleri:\n\n"
    for task in daily_tasks:
        task_id = str(task["id"])
        data[today]["tasks"][task_id] = False
        msg += f"{task['id']}. {task['name']} → {task['source']}\n"
        msg += f"Cevap için: yaptım{task['id']}\n\n"

    # Haftada 2-3 gün ekstra görev
    weekday = datetime.now(tz).weekday()
    if weekday in [1,3,5]:  # Pazartesi, Çarşamba, Cuma
        for task in extra_tasks:
            task_id = str(task["id"])
            data[today]["tasks"][task_id] = False
            msg += f"{task['id']}. {task['name']} → {task['source']}\n"
            msg += f"Cevap için: yaptım{task['id']}\n\n"

    save_data(data)
    send_message(msg)

# ------------------ Görev Tamamlama ------------------
def check_task_completion(message):
    data = load_data()
    today = get_today_key()

    if today not in data:
        return

    for task in daily_tasks + extra_tasks:
        cmd = f"yaptım{task['id']}"
        if message.lower() == cmd.lower():
            data[today]["tasks"][str(task['id'])] = True
            send_message(f"{task['name']} görevi kaydedildi ✅")
            save_data(data)
            return

# ------------------ Hatırlatma ------------------
def remind_tasks():
    data = load_data()
    today = get_today_key()
    if today not in data:
        return

    incomplete = [t for t, done in data[today]["tasks"].items() if not done]
    if incomplete:
        msg = "⏰ Hala tamamlamadığınız görevler var:\n"
        for t_id in incomplete:
            task_name = next((t["name"] for t in daily_tasks + extra_tasks if str(t["id"]) == t_id), "")
            msg += f"- {task_name} → Cevap için: yaptım{t_id}\n"
        send_message(msg)

# ------------------ Haftalık Özet ------------------
def weekly_summary():
    data = load_data()
    today = datetime.now(tz)
    week_start = today - timedelta(days=today.weekday())
    week_dates = [(week_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    total_tasks = 0
    completed_tasks = 0
    msg = "📊 Haftalık Görev Özetiniz:\n"
    for day in week_dates:
        if day in data:
            day_tasks = data[day]["tasks"]
            total_tasks += len(day_tasks)
            completed_tasks += sum(1 for done in day_tasks.values() if done)
            day_msg = f"{day}: {sum(1 for done in day_tasks.values() if done)}/{len(day_tasks)} görev tamamlandı"
            msg += day_msg + "\n"

    msg += f"\nToplam: {completed_tasks}/{total_tasks} görev tamamlandı ✅"
    send_message(msg)

# ------------------ Eksik Görevler İçin Ertesi Gün Hatırlatma ------------------
def remind_previous_day():
    data = load_data()
    yesterday = (datetime.now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")
    if yesterday not in data:
        return

    incomplete = [t for t, done in data[yesterday]["tasks"].items() if not done]
    if incomplete:
        msg = f"⚠️ Dün tamamlamadığınız görevler:\n"
        for t_id in incomplete:
            task_name = next((t["name"] for t in daily_tasks + extra_tasks if str(t["id"]) == t_id), "")
            msg += f"- {task_name} → Cevap için: yaptım{t_id}\n"
        send_message(msg)

# ------------------ Mini Test ------------------
def weekly_mini_test():
    msg = "📝 Haftalık Mini Test!\n- Kısa bir okuma yapın ve 5 kelime yazın\n- 3 kısa cümle yazın\nCevaplarınızı yaptım1, yaptım2 vs ile bildirin"
    send_message(msg)

# ------------------ Scheduler ------------------
scheduler.add_job(send_daily_tasks, 'cron', hour=17, minute=0)  # Günlük görevler
scheduler.add_job(remind_tasks, 'interval', hours=1)  # Saatte 1 hatırlatma
scheduler.add_job(weekly_summary, 'cron', day_of_week='sun', hour=18, minute=0)  # Haftalık özet
scheduler.add_job(remind_previous_day, 'cron', hour=9, minute=0)  # Eksik görev hatırlatma
scheduler.add_job(weekly_mini_test, 'cron', day_of_week='sun', hour=19, minute=0)  # Mini test

scheduler.start()

# ------------------ Kullanıcı Mesaj Kontrolü ------------------
def listen_for_input():
    last_update_id = None
    while True:
        updates = bot.get_updates(offset=last_update_id, timeout=10)
        for update in updates:
            if update.message and update.message.text:
                check_task_completion(update.message.text)
            last_update_id = update.update_id + 1

if __name__ == "__main__":
    send_message("✅ İngilizce çalışma botu başlatıldı!")
    listen_for_input()
