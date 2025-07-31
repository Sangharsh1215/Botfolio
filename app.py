import streamlit as st
import pandas as pd
from bot4 import (
    fetch_intraday_data,
    add_indicators,
    add_advanced_indicators,
    generate_advanced_signal,
    log_signal,
    send_telegram_message
)

st.set_page_config(page_title="Stock Monitor", layout="wide")
st.title("📊 NSE Stock Monitoring Bot")

# === Telegram Config Inputs ===
st.sidebar.header("🔐 Telegram Settings")
bot_token = st.sidebar.text_input("Enter your Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Enter your Telegram Chat ID")

# === Load ticker list ===
@st.cache_data
def load_ticker_list(csv_path="tickers_list.csv"):
    return pd.read_csv(csv_path)

df = load_ticker_list()

# === Ticker Selection ===
selected_names = st.multiselect(
    "✅ Select stocks to monitor:",
    options=df["NAME"] + " (" + df["TICKER"] + ")"
)

if st.button("🚀 Start Monitoring"):
    if not selected_names:
        st.warning("Please select at least one ticker.")
    elif not bot_token or not chat_id:
        st.warning("Please enter both your Telegram Bot Token and Chat ID.")
    else:
        selected_tickers = [name.split("(")[-1].replace(")", "") for name in selected_names]
        all_signals = []

        with st.spinner("Fetching data and generating signals..."):
            for ticker in selected_tickers:
                try:
                    st.write(f"🔍 Processing: `{ticker}`")
                    df_data = fetch_intraday_data(ticker)
                    df_data = add_indicators(df_data)
                    df_data = add_advanced_indicators(df_data)

                    # Commented out saving CSV to disk
                    # df_data.to_csv(f"{ticker}_indicators.csv")

                    signal, price = generate_advanced_signal(df_data)
                    message = f"{signal} signal for {ticker} at ₹{price:.2f}" if price else f"{signal} signal for {ticker} (price N/A)"
                    st.success(message)
                    all_signals.append(message)
                    log_signal(ticker, signal, price)

                except Exception as e:
                    error_msg = f"❌ Error for {ticker}: {e}"
                    st.error(error_msg)
                    all_signals.append(error_msg)

        final_msg = "📡 Signal Summary:\n\n" + "\n".join(all_signals)
        send_telegram_message(final_msg, bot_token, chat_id)

        st.balloons()
        st.info("Signals sent to your Telegram.")
