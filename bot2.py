import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
from collections import defaultdict

# --- Telegram Setup ---
BOT_TOKEN = "8120831257:AAHR4QZyDRyH6Am0bK6OhDiJUPyqc-PCitU"
CHAT_ID = "940705270"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except Exception as e:
        print("Telegram error:", e)
        return False

# --- Data Fetching ---
def fetch_intraday_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if df.empty:
            return None
        return df
    except:
        return None

# --- Indicators ---
def add_indicators(df):
    df = df.copy()
    df["EMA_20"] = ta.ema(df["Close"], length=20)
    df["RSI"] = ta.rsi(df["Close"], length=14)
    macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd is not None:
        df["MACD"] = macd["MACD_12_26_9"]
        df["MACD_signal"] = macd["MACDs_12_26_9"]
    return df.dropna()

# --- Signal Generation ---
def generate_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = last["Close"]

    if last["RSI"] < 30 and prev["MACD"] < prev["MACD_signal"] and last["MACD"] > last["MACD_signal"]:
        return "BUY", price
    elif last["RSI"] > 70 and prev["MACD"] > prev["MACD_signal"] and last["MACD"] < last["MACD_signal"]:
        return "SELL", price
    else:
        return "HOLD", price

# --- Volatility Filter ---
def is_volatile_and_active(df):
    if df.empty or len(df) < 20:
        return False
    last_vol = df.iloc[-1]["Volume"]
    mean_vol = df["Volume"].mean()
    price_range = df["High"].max() - df["Low"].min()
    return last_vol > mean_vol * 1.5 and price_range > df["Close"].mean() * 0.01

# --- Summary Collector ---
signal_summary = defaultdict(list)

def send_hourly_summary():
    summary_lines = [f"📊 Hourly Stock Signal Summary"]
    for ticker, signals in signal_summary.items():
        if signals:
            summary_lines.append(f"{ticker}: {', '.join(signals)}")
    if len(summary_lines) == 1:
        summary_lines.append("No significant signals this hour.")
    send_telegram_message("\n".join(summary_lines))
    signal_summary.clear()

# --- Tickers ---
tickers = [
    "INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "WIPRO.NS", "HCLTECH.NS"
]

# --- Main Loop ---
def run_bot():
    start_time = time.time()
    while True:
        for ticker in tickers:
            try:
                df = fetch_intraday_data(ticker)
                if df is None:
                    continue
                df = add_indicators(df)
                if not is_volatile_and_active(df):
                    continue
                signal, price = generate_signal(df)
                if price:
                    signal_summary[ticker].append(f"{signal} @ ₹{price:.2f}")
            except Exception as e:
                print(f"Error for {ticker}: {e}")

        if time.time() - start_time >= 3600:  # every hour
            send_hourly_summary()
            start_time = time.time()

        time.sleep(60)  # check every minute

# --- Start Bot ---
run_bot()
