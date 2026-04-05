import sys
import asyncio
from flask import Flask, request, jsonify
from aiogram import types
import main

app = Flask(__name__)
bot = main.bot
dp = main.dp

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = types.Update.to_object(types.Update, **request.json)
    await dp.process_update(update)
    return jsonify({"status": "ok"})

async def on_startup():
    webhook_url = 'https://YOUR_USERNAME.pythonanywhere.com/webhook'  # O‘zgartiring!
    await bot.set_webhook(webhook_url)
    print("Webhook o‘rnatildi")

@app.before_first_request
def startup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(on_startup())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host='0.0.0.0', port=8000)
