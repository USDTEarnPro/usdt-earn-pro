from flask import Flask, render_template, request, jsonify
import telebot
import os
from pymongo import MongoClient

app = Flask(__name__, template_folder='.')
BOT_TOKEN = '9057837958:AAF5rqXdNflZXoejHktaVh7HLCokEUMxJEA' 
bot = telebot.TeleBot(BOT_TOKEN)

# এখানে আপনার MongoDB এর লিংক বসান (পাসওয়ার্ড সহ)
MONGO_URI = "mongodb+srv://admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"

# ডাটাবেস কানেক্ট করা
client = MongoClient(MONGO_URI)
db = client['usdt_bot_db']
users_collection = db['users']

@app.route('/')
def index():
    return render_template('index.html')

# ইউজারের ডাটা আনা
@app.route('/api/get_user', methods=['POST'])
def get_user():
    data = request.json
    user_id = str(data.get('user_id'))
    name = data.get('name')
    
    user = users_collection.find_one({"user_id": user_id})
    
    if user is None:
        # নতুন ইউজার তৈরি
        new_user = {
            "user_id": user_id, 
            "name": name, 
            "balance": 0.0, 
            "missions_done": 0, 
            "joined_channel": 0,
            "refs": 0
        }
        users_collection.insert_one(new_user)
        balance, missions, joined, refs = 0.0, 0, 0, 0
    else:
        balance = user.get("balance", 0.0)
        missions = user.get("missions_done", 0)
        joined = user.get("joined_channel", 0)
        refs = user.get("refs", 0)
        
    return jsonify({"balance": balance, "missions": missions, "joined": joined, "refs": refs})

# চ্যানেল ভেরিফাই করা
@app.route('/api/verify_mission', methods=['POST'])
def verify_mission():
    data = request.json
    user_id = str(data.get('user_id'))
    
    user = users_collection.find_one({"user_id": user_id})
    
    if user and user.get("joined_channel", 0) == 0:
        # ব্যালেন্স আপডেট
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": 0.010, "missions_done": 1}, "$set": {"joined_channel": 1}}
        )
        return jsonify({"status": "success", "message": "Mission verified! +0.010 USDT added."})
    
    return jsonify({"status": "error", "message": "Already verified or user not found."})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to USDT EARN PRO! Click the button below to open the app.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
