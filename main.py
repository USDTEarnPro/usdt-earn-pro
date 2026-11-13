from flask import Flask, render_template, request, jsonify
import telebot
import os
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__, template_folder='.')
# আপনার নতুন বটের টোকেন
BOT_TOKEN = '9127167452:AAHshYnF_2aRCa8zGgE6GvVHBTfSL9HBakM' 
# এখানে আপনার টেলিগ্রাম আইডি বসান (যেমন: 123456789)
ADMIN_ID = 123456789 
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার MongoDB লিংক
MONGO_URI = "mongodb+srv://mrhasan77722_db_user:FQYHQ67tI37CGkTm@cluster0.4tam4es.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['usdt_bot_db']
users_col = db['users']
history_col = db['history']
withdraw_col = db['withdrawals']

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
        
        user = users_col.find_one({"user_id": user_id})
        if not user:
            users_col.insert_one({"user_id": user_id, "name": name, "balance": 0.0, "missions": 0, "joined": 0, "refs": 0})
            
            if referrer_id and referrer_id != user_id:
                if users_col.find_one({"user_id": referrer_id}):
                    users_col.update_one({"user_id": referrer_id}, {"$inc": {"refs": 1, "balance": 0.050}})
                    history_col.insert_one({"user_id": referrer_id, "task": "Referral Bonus", "amount": 0.050, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            user = users_col.find_one({"user_id": user_id})
            
        history = list(history_col.find({"user_id": user_id}).sort("_id", -1).limit(10))
        history_data = [{"task": h["task"], "amount": h["amount"], "time": h["time"]} for h in history]
        
        return jsonify({"status": "success", "balance": user["balance"], "missions": user["missions"], "joined": user["joined"], "refs": user["refs"], "history": history_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        user = users_col.find_one({"user_id": user_id})
        
        if user and user["joined"] == 0:
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": 0.010, "missions": 1}, "$set": {"joined": 1}})
            history_col.insert_one({"user_id": user_id, "task": "Joined Channel", "amount": 0.010, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            return jsonify({"status": "success", "message": "Mission verified! +0.010 USDT added."})
        return jsonify({"status": "error", "message": "Already verified."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/request_withdraw', methods=['POST'])
def request_withdraw():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        amount = float(data.get('amount'))
        
        user = users_col.find_one({"user_id": user_id})
        if user and user["refs"] >= 10 and amount <= user["balance"] and amount >= 0.01:
            withdraw_col.insert_one({"user_id": user_id, "address": data['address'], "amount": amount, "status": "Pending", "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            try:
                bot.send_message(ADMIN_ID, f"🚨 নতুন উইথড্র!\nইউজার: {user['name']} (ID: {user_id})\nঅ্যামাউন্ট: {amount} USDT\nঅ্যাড্রেস: `{data['address']}`", parse_mode='Markdown')
            except: pass
            return jsonify({"status": "success", "message": "Withdraw request sent to admin."})
        return jsonify({"status": "error", "message": "Requirements not met."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # সুন্দর টেক্সট ও ওপেন অ্যাপ বাটন
    from telebot import types
    markup = types.InlineKeyboardMarkup()
    web_app_url = "https://usdt-earn-pro.onrender.com"
    web_app_btn = types.InlineKeyboardButton(text="💎 Open App", web_app=types.WebAppInfo(url=web_app_url))
    markup.add(web_app_btn)
    
    welcome_text = (
        "💎 <b>WELCOME TO GRAM X PRO</b>\n"
        "<i>Your Journey. Your Rewards. Your Future.</i>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚡️ <b>UNLOCK YOUR POTENTIAL</b>\n"
        "➡️ <b>EXPLORE</b> — Discover new opportunities\n"
        "💰 <b>EARN</b> — Get rewarded for your efforts\n"
        "👍 <b>WITHDRAW</b> — Cash out when eligible\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>YOUR JOURNEY STARTS HERE</b>\n"
        "✅ <i>Every task brings a new opportunity. Are you ready to begin?</i>\n"
        "🤑 <b>ENTER THE WORLD OF USDT EARN PRO</b>"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='HTML')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
