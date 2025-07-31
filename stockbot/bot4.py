import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# === Telegram config ===
BOT_TOKEN = "8120831257:AAHR4QZyDRyH6Am0bK6OhDiJUPyqc-PCitU"
CHAT_ID = "940705270"

# === User Ticker Selection ===
def get_user_selected_tickers(csv_file="stockbot/tickers_list.csv"):
    df = pd.read_csv(csv_file)
    print("\n📋 Available Stocks:")
    for idx, row in df.iterrows():
        print(f"{idx + 1}. {row['NAME']} ({row['TICKER']})")

    selected = input("\n🔢 Enter comma-separated numbers for tickers to monitor (e.g., 1,3,5): ")
    try:
        indices = [int(i.strip()) - 1 for i in selected.split(",")]
        selected_tickers = df.iloc[indices]["TICKER"].tolist()
        return selected_tickers
    except Exception as e:
        print(f"❌ Invalid input: {e}")
        return []

# === Telegram Messaging ===
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

# === Data Fetching & Indicators ===
def fetch_intraday_data(ticker):
    print(f"🔍 Fetching data for {ticker}...")
    df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
    df.dropna(inplace=True)
    print(f"✅ {ticker} data shape: {df.shape}")
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
    print("📊 Basic indicators added.")
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
    print("🔬 Advanced indicators added.")
    return df

def generate_advanced_signal(df):
    if len(df) < 2:
        return "HOLD", None

    last = df.iloc[[-1]]
    prev = df.iloc[[-2]]

    try:
        rsi = float(last["RSI"].iloc[0])
        macd = float(last["MACD"].iloc[0])
        macd_sig = float(last["MACD_signal"].iloc[0])
        price = float(last["Close"].iloc[0])
        vwap = float(last["VWAP"].iloc[0])

        if rsi < 45 and macd > macd_sig and price < vwap:
            return "BUY", price
        elif rsi > 60 and macd < macd_sig and price > vwap:
            return "SELL", price
        return "HOLD", price

    except Exception as e:
        print("⚠️ Signal error:", e)
        return "HOLD", None

# === Main Execution ===
if __name__ == "__main__":
    selected_tickers = get_user_selected_tickers()

    if not selected_tickers:
        print("⚠️ No tickers selected. Exiting.")
        exit()

    all_signals = []

    for ticker in selected_tickers:
        try:
            print(f"\n🔍 Processing: {ticker}")
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

    final_msg = "📡 Signal Summary:\n\n" + "\n".join(all_signals)
    send_telegram_message(final_msg)
