import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# Telegram config (disabled for notebook testing)
BOT_TOKEN = "8120831257:AAHR4QZyDRyH6Am0bK6OhDiJUPyqc-PCitU"
CHAT_ID = "940705270"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except:
        return False

def log_signal(ticker, signal, price):
    with open("trade_signals_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), ticker, signal, price])
    print(f"📝 Logged: {ticker} | {signal} | ₹{price:.2f}")

def fetch_intraday_data(ticker):
    print(f"🔍 Fetching data for {ticker}...")
    df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
    df.dropna(inplace=True)
    print(f"✅ {ticker} data shape: {df.shape}")
    return df

def add_indicators(df):
    df = df.copy()

    # EMA
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # RSI
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df.dropna(inplace=True)
    print("📊 Basic indicators added.")
    return df

def add_advanced_indicators(df):
    df = df.copy()

    df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()

    # Bollinger Bands
    df["BB_MID"] = df["Close"].rolling(window=20).mean()
    df["BB_STD"] = df["Close"].rolling(window=20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * df["BB_STD"]
    df["BB_LOWER"] = df["BB_MID"] - 2 * df["BB_STD"]

    # ATR
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift())
    df["L-PC"] = abs(df["Low"] - df["Close"].shift())
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(window=14).mean()
    df.drop(["H-L", "H-PC", "L-PC", "TR"], axis=1, inplace=True)

    df.dropna(inplace=True)
    print("🔬 Advanced indicators added.")
    return df

def generate_advanced_signal(df):
    if len(df) < 2:
        return "HOLD", None

    last = df.iloc[[-1]]  # Keep as DataFrame to support .iloc[0]
    prev = df.iloc[[-2]]

    try:
        rsi = float(last["RSI"].iloc[0])
        macd = float(last["MACD"].iloc[0])
        macd_sig = float(last["MACD_signal"].iloc[0])
        price = float(last["Close"].iloc[0])
        vwap = float(last["VWAP"].iloc[0])

        # Relaxed condition for testing
        if rsi < 45 and macd > macd_sig and price < vwap:
            return "BUY", price
        elif rsi > 60 and macd < macd_sig and price > vwap:
            return "SELL", price
        return "HOLD", price

    except Exception as e:
        print("⚠️ Signal error:", e)
        return "HOLD", None

# List of volatile tickers
tickers = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ADANIGREEN.NS", "WIPRO.NS",
    "POWERGRID.NS", "ONGC.NS", "ULTRACEMCO.NS", "ASIANPAINT.NS", "MARUTI.NS"
]

all_signals = []  # For Telegram summary

for ticker in tickers:
    try:
        print(f"\n🔍 Fetching: {ticker}")
        df = fetch_intraday_data(ticker)
        df = add_indicators(df)
        df = add_advanced_indicators(df)

        df.to_csv(f"{ticker}_indicators.csv")
        print(f"💾 Saved {ticker}_indicators.csv")

        signal, price = generate_advanced_signal(df)

        if price:
            signal_msg = f"{signal} signal for {ticker} at ₹{price:.2f}"
        else:
            signal_msg = f"{signal} signal for {ticker} (price N/A)"

        print(signal_msg)
        all_signals.append(signal_msg)

        log_signal(ticker, signal, price)

    except Exception as e:
        error_msg = f"❌ Error for {ticker}: {e}"
        print(error_msg)
        all_signals.append(error_msg)

# Send all results in one combined message
final_msg = "📡 Signal Summary:\n\n" + "\n".join(all_signals)
send_telegram_message(final_msg)