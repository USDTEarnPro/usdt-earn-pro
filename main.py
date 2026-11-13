from flask import Flask, render_template, request, jsonify
import telebot
import os
import sqlite3
from datetime import datetime

app = Flask(__name__, template_folder='.')
BOT_TOKEN = '9057837958:AAF5rqXdNflZXoejHktaVh7HLCokEUMxJEA' 
bot = telebot.TeleBot(BOT_TOKEN)

def get_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # ইউজার টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id TEXT PRIMARY KEY, name TEXT, balance REAL DEFAULT 0.0, missions_done INTEGER DEFAULT 0, joined_channel INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)''')
    # হিস্ট্রি টেবিল (নতুন)
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, task_name TEXT, amount REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_user', methods=['POST'])
def get_user():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        name = data.get('name')
        referrer_id = data.get('referrer_id') 
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance, missions_done, joined_channel, refs FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        
        if user is None:
            # নতুন ইউজার তৈরি
            c.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
            
            # রেফারেল লজিক (সঠিকভাবে)
            if referrer_id and referrer_id != user_id:
                c.execute("SELECT user_id FROM users WHERE user_id=?", (referrer_id,))
                if c.fetchone():
                    # রেফারারকে ০.০৫০ USDT বোনাস ও ১ জন কাউন্ট
                    c.execute("UPDATE users SET refs = refs + 1, balance = balance + 0.050 WHERE user_id=?", (referrer_id,))
                    # রেফারারের হিস্ট্রিতে সেভ
                    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO history (user_id, task_name, amount, timestamp) VALUES (?, ?, ?, ?)", 
                              (referrer_id, f"Referral Bonus ({name})", 0.050, time_now))
                    
            conn.commit()
            balance, missions, joined, refs = 0.0, 0, 0, 0
        else:
            balance, missions, joined, refs = user
            
        # হিস্ট্রি ডাটা আনা
        c.execute("SELECT task_name, amount, timestamp FROM history WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
        history_data = [{"task": row[0], "amount": row[1], "time": row[2]} for row in c.fetchall()]
        
        conn.close()
        return jsonify({"balance": balance, "missions": missions, "joined": joined, "refs": refs, "history": history_data})
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT joined_channel FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        
        if user and user[0] == 0:
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("UPDATE users SET balance = balance + 0.010, missions_done = missions_done + 1, joined_channel = 1 WHERE user_id=?", (user_id,))
            c.execute("INSERT INTO history (user_id, task_name, amount, timestamp) VALUES (?, ?, ?, ?)", 
                      (user_id, "Joined SABX Earn BD", 0.010, time_now))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Mission verified! +0.010 USDT added."})
        
        conn.close()
        return jsonify({"status": "error", "message": "Already verified or user not found."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ভবিষ্যতের জন্য অ্যাড রিওয়ার্ড API (এখন বাটন নেই, তবে কোড ঠিক আছে)
@app.route('/api/add_ad_reward', methods=['POST'])
def add_ad_reward():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        conn = get_db()
        c = conn.cursor()
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("UPDATE users SET balance = balance + 0.001 WHERE user_id=?", (user_id,))
        c.execute("INSERT INTO history (user_id, task_name, amount, timestamp) VALUES (?, ?, ?, ?)", 
                  (user_id, "Watched Ad", 0.001, time_now))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Ad reward added!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to USDT EARN PRO! Click the button below to open the app.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
