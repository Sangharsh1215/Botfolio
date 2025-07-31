import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import time
import csv

# Telegram config
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        print("📨 Telegram sent:", response.status_code)
        return response.status_code == 200
    except Exception as e:
        print("❌ Telegram error:", e)
        return False

def log_signal(ticker, signal, price):
    with open("trade_signals_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), ticker, signal, price])
    print(f"📝 Logged: {ticker} | {signal} | ₹{price:.2f}" if price else f"📝 Logged: {ticker} | {signal}")

def fetch_intraday_data(ticker):
    print(f"🔍 Fetching data for {ticker}...")
    df = yf.download(ticker, period="1d", interval="1m", progress=False)
    df.dropna(inplace=True)
    if df.empty:
        raise ValueError("No data returned")
    return df

def add_indicators(df):
    df = df.copy()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df.dropna(inplace=True)
    return df

def add_advanced_indicators(df):
    df = df.copy()
    df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()
    df["BB_MID"] = df["Close"].rolling(window=20).mean()
    df["BB_STD"] = df["Close"].rolling(window=20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * df["BB_STD"]
    df["BB_LOWER"] = df["BB_MID"] - 2 * df["BB_STD"]
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift())
    df["L-PC"] = abs(df["Low"] - df["Close"].shift())
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(window=14).mean()
    df.drop(["H-L", "H-PC", "L-PC", "TR"], axis=1, inplace=True)
    df.dropna(inplace=True)
    return df

def generate_advanced_signal(df):
    if len(df) < 2:
        return "HOLD", None
    last = df.iloc[-1]
    try:
        rsi = float(last["RSI"])
        macd = float(last["MACD"])
        macd_sig = float(last["MACD_signal"])
        price = float(last["Close"])
        vwap = float(last["VWAP"])
        if rsi < 45 and macd > macd_sig and price < vwap:
            return "BUY", price
        elif rsi > 60 and macd < macd_sig and price > vwap:
            return "SELL", price
        return "HOLD", price
    except Exception as e:
        print("⚠️ Signal generation error:", e)
        return "HOLD", None

# 🔽 Load selected tickers
try:
    with open("selected_tickers.txt") as f:
        tickers = [line.strip() for line in f.readlines() if line.strip()]
except Exception as e:
    print("🚫 Could not read selected_tickers.txt:", e)
    tickers = []

print("📡 Starting scan for:", tickers)
all_signals = []

for ticker in tickers:
    try:
        df = fetch_intraday_data(ticker)
        df = add_indicators(df)
        df = add_advanced_indicators(df)
        signal, price = generate_advanced_signal(df)
        df.to_csv(f"{ticker}_indicators.csv")
        msg = f"{signal} signal for {ticker} at ₹{price:.2f}" if price else f"{signal} signal for {ticker} (price N/A)"
        print(msg)
        all_signals.append(msg)
        log_signal(ticker, signal, price)
    except Exception as e:
        error_msg = f"❌ Error for {ticker}: {e}"
        print(error_msg)
        all_signals.append(error_msg)

# Send combined Telegram alert
final_msg = "📡 Signal Summary:\n\n" + "\n".join(all_signals)
print("📬 Sending Telegram Summary...")
print(final_msg)
send_telegram_message(final_msg)
