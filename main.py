from flask import Flask, render_template, request, jsonify
import telebot
import os
from pymongo import MongoClient
from datetime import datetime
from telebot import types

app = Flask(__name__, template_folder='.')

BOT_TOKEN = '9127167452:AAHshYnF_2aRCa8zGgE6GvVHBTfSL9HBakM' 
ADMIN_ID = 123456789 # আপনার টেলিগ্রাম আইডি
bot = telebot.TeleBot(BOT_TOKEN)

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
            users_col.insert_one({
                "user_id": user_id, "name": name, "balance": 0.0, 
                "missions": 0, "joined": 0, "joined2": 0, "refs": 0
            })
            
            if referrer_id and referrer_id != user_id:
                referrer = users_col.find_one({"user_id": referrer_id})
                if referrer:
                    users_col.update_one({"user_id": referrer_id}, {"$inc": {"refs": 1, "balance": 0.050}})
                    history_col.insert_one({
                        "user_id": referrer_id, "task": "Referral Bonus", 
                        "amount": 0.050, "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
            
            user = users_col.find_one({"user_id": user_id})
            
        history = list(history_col.find({"user_id": user_id}).sort("_id", -1).limit(10))
        history_data = [{"task": h["task"], "amount": h["amount"], "time": h["time"]} for h in history]
        
        return jsonify({
            "status": "success", 
            "balance": float(user.get("balance", 0.0)), 
            "missions": int(user.get("missions", 0)), 
            "joined": int(user.get("joined", 0)), 
            "joined2": int(user.get("joined2", 0)), 
            "refs": int(user.get("refs", 0)), 
            "history": history_data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# নতুন রুট: ইউজারের উইথড্র হিস্ট্রি আনা
@app.route('/api/get_withdrawals', methods=['POST'])
def get_withdrawals():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        withdrawals = list(withdraw_col.find({"user_id": user_id}).sort("_id", -1))
        wd_data = [{"amount": w["amount"], "status": w["status"], "time": w["time"]} for w in withdrawals]
        return jsonify({"status": "success", "withdrawals": wd_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        user = users_col.find_one({"user_id": user_id})
        
        if user and user.get("joined", 0) == 0:
            users_col.update_one(
                {"user_id": user_id}, 
                {"$inc": {"balance": 0.010, "missions": 1}, "$set": {"joined": 1}}
            )
            history_col.insert_one({
                "user_id": user_id, "task": "Joined SABX Earn BD", 
                "amount": 0.010, "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            return jsonify({"status": "success", "message": "Mission verified! +0.010 USDT added."})
        return jsonify({"status": "error", "message": "Already verified."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/verify_mission2', methods=['POST'])
def verify_mission2():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        user = users_col.find_one({"user_id": user_id})
        
        if user and user.get("joined2", 0) == 0:
            users_col.update_one(
                {"user_id": user_id}, 
                {"$inc": {"balance": 0.010, "missions": 1}, "$set": {"joined2": 1}}
            )
            history_col.insert_one({
                "user_id": user_id, "task": "Joined SX EARN PRO", 
                "amount": 0.010, "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
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
        address = data.get('address')
        
        user = users_col.find_one({"user_id": user_id})
        if user and user.get("refs", 0) >= 10 and amount <= user.get("balance", 0.0) and amount >= 0.01:
            withdraw_col.insert_one({
                "user_id": user_id, "name": user.get("name"), "address": address, 
                "amount": amount, "status": "Pending", "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            try:
                bot.send_message(ADMIN_ID, f"🚨 New Withdraw Request!\n👤 Name: {user.get('name')}\n🆔 ID: `{user_id}`\n💰 Amount: {amount} USDT\n📍 Address: `{address}`\n\nTo Pay: `/pay {user_id} {amount}`", parse_mode='Markdown')
            except: pass
            return jsonify({"status": "success", "message": "Withdraw request sent to admin."})
        return jsonify({"status": "error", "message": "Requirements not met or insufficient balance."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    web_app_btn = types.InlineKeyboardButton(text="💎 Open App", web_app=types.WebAppInfo(url="https://usdt-earn-pro.onrender.com"))
    markup.add(web_app_btn)
    bot.reply_to(message, "👇 Click below to open the app", reply_markup=markup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
