import requests
import pandas as pd
import time
import logging
from datetime import datetime

# تنظیمات لاگ
logging.basicConfig(
    filename="signal_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# API صرافی غیرمتمرکز سولانا (Raydium)
DEX_API = "https://api.raydium.io/pairs"
TELEGRAM_BOT_TOKEN = "8060904155:AAHp8TMdN16xlD942pcZKNclOCgAWSyGJHg"
TELEGRAM_CHAT_ID = "1290658065"


# 1. دریافت داده از Raydium
def fetch_dex_data():
    try:
        logging.info("Fetching data from Raydium API...")
        response = requests.get(DEX_API)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return []


# 2. تحلیل داده‌ها و رتبه‌بندی
def analyze_data(data):
    try:
        logging.info("Analyzing data...")
        
        # تبدیل داده‌ها به DataFrame
        df = pd.DataFrame(data)
        
        # فیلتر کردن توکن‌های شبکه سولانا (فقط SOL جفت‌ها)
        solana_pairs = df[df['base'] == 'SOL']

        # افزودن امتیاز سیگنال خرید
        solana_pairs['signal_score'] = (
            solana_pairs['priceChange24h'].astype(float) * 0.4 +  # تغییر قیمت 24 ساعت
            solana_pairs['volume24h'].astype(float) * 0.3 +  # حجم معاملات
            solana_pairs['liquidity'].astype(float) * 0.3  # نقدینگی
        )

        # مرتب‌سازی بر اساس سیگنال
        top_signals = solana_pairs.sort_values(by='signal_score', ascending=False).head(5)

        return top_signals[['name', 'symbol', 'price', 'priceChange24h', 'volume24h', 'signal_score']]
    except Exception as e:
        logging.error(f"Error analyzing data: {e}")
        return pd.DataFrame()


# 3. ارسال سیگنال‌ها به تلگرام
def send_signals_to_telegram(coins):
    try:
        if coins.empty:
            logging.warning("No coins to send!")
            return

        message = "🚀 سیگنال خرید میم‌کوین‌های سولانا:\n\n"
        for _, row in coins.iterrows():
            message += f"🔹 {row['name']} ({row['symbol']})\n"
            message += f"💰 قیمت: ${row['price']}\n"
            message += f"📈 رشد 24 ساعت: {row['priceChange24h']}%\n"
            message += f"📊 حجم معاملات: ${int(row['volume24h']):,}\n"
            message += f"🌟 امتیاز سیگنال: {row['signal_score']:.2f}\n\n"

        # ارسال پیام به تلگرام
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, params=params)
        response.raise_for_status()
        logging.info("Signal sent to Telegram!")
    except Exception as e:
        logging.error(f"Error sending signals to Telegram: {e}")


# 4. اجرای برنامه
def main():
    while True:
        logging.info("Starting new cycle...")
        data = fetch_dex_data()
        if data:
            top_signals = analyze_data(data)
            send_signals_to_telegram(top_signals)
        else:
            logging.warning("No data fetched this cycle.")

        # زمان‌بندی (هر 30 دقیقه)
        time.sleep(1800)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")
