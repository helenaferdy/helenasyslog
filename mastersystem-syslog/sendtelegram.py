import telegram

TELEGRAM_BOT_TOKEN = '6338264144:AAGSmQIXQkXTFt9L4cfSHi6751lEoGwnYXQ'

async def send_telegram(message, chat_id):
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        ## add await on linux
        await bot.send_message(chat_id=chat_id, text=message)
        print("* Telegram message sent")
        return True
    except Exception as e:
        print(f"* Failed sending telegram message {e}")
        return False