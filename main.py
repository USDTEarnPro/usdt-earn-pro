from flask import Flask, render_template, request, jsonify
import telebot
import os
import sqlite3

app = Flask(__name__, template_folder='.')
# আপনার বটের টোকেন
BOT_TOKEN = '9057837958:AAF5rqXdNflZXoejHktaVh7HLCokEUMxJEA' 
bot = telebot.TeleBot(BOT_TOKEN)

# ডাটাবেস তৈরি করা
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id TEXT PRIMARY KEY, name TEXT, balance REAL DEFAULT 0.0, missions_done INTEGER DEFAULT 0, joined_channel INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# ইউজারের ডাটা আনা (অ্যাপ ওপেন হলে)
@app.route('/api/get_user', methods=['POST'])
def get_user():
    data = request.json
    user_id = str(data.get('user_id'))
    name = data.get('name')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT balance, missions_done, joined_channel FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    
    if user is None:
        c.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        balance, missions, joined = 0.0, 0, 0
    else:
        balance, missions, joined = user
        
    conn.close()
    return jsonify({"balance": balance, "missions": missions, "joined": joined})

# চ্যানেল ভেরিফাই করা (ব্যালেন্স যোগ করা)
@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    data = request.json
    user_id = str(data.get('user_id'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT joined_channel FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    
    if user and user[0] == 0:
        c.execute("UPDATE users SET balance = balance + 0.010, missions_done = missions_done + 1, joined_channel = 1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Mission verified! +0.010 USDT added."})
    
    conn.close()
    return jsonify({"status": "error", "message": "Already verified or user not found."})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to USDT EARN PRO! Click the button below to open the app.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
