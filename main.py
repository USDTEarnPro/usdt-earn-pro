from flask import Flask, render_template, request, jsonify
import telebot
import os
import sqlite3

app = Flask(__name__, template_folder='.')
BOT_TOKEN = '9057837958:AAF5rqXdNflZXoejHktaVh7HLCokEUMxJEA' 
bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, balance REAL DEFAULT 0.0, missions_done INTEGER DEFAULT 0, joined_channel INTEGER DEFAULT 0, refs INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_user', methods=['POST'])
def get_user():
    data = request.json
    user_id = str(data.get('user_id'))
    name = data.get('name')
    referrer_id = data.get('referrer_id') 
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT balance, missions_done, joined_channel, refs FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    
    if user is None:
        c.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
        
        if referrer_id and referrer_id != user_id:
            c.execute("SELECT user_id FROM users WHERE user_id=?", (referrer_id,))
            if c.fetchone():
                c.execute("UPDATE users SET refs = refs + 1 WHERE user_id=?", (referrer_id,))
                c.execute("UPDATE users SET balance = balance + 0.050 WHERE user_id=?", (referrer_id,))
                
        conn.commit()
        balance, missions, joined, refs = 0.0, 0, 0, 0
    else:
        balance, missions, joined, refs = user
        
    conn.close()
    return jsonify({"balance": balance, "missions": missions, "joined": joined, "refs": refs})

@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    data = request.json
    user_id = str(data.get('user_id'))
    
    conn = sqlite3.connect('users.db')
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

@app.route('/api/add_ad_reward', methods=['POST'])
def add_ad_reward():
    data = request.json
    user_id = str(data.get('user_id'))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + 0.001 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Ad reward added!"})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to USDT EARN PRO! Click the button below to open the app.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
