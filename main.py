from flask import Flask, render_template, request
import telebot
import os

app = Flask(__name__, template_folder='.')

# আপনার টোকেন নিচে বসানো হয়েছে
BOT_TOKEN = '9057837958:AAF5rqXdNflZXoejHktaVh7HLCokEUMxJEA' 
bot = telebot.TeleBot(BOT_TOKEN)

@app.route('/')
def index():
    return render_template('index.html')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to USDT EARN PRO! Click the button below to open the app.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
