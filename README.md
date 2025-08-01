
# 🤖 Botfolio

> *"It’s not a portfolio. It’s a lifestyle."*

**Botfolio** is a smart, slightly sarcastic NSE stock monitoring bot that uses technical indicators to generate signals (BUY/SELL/HOLD) and delivers them straight to your **Telegram** inbox — every hour. It features a Streamlit UI, technical analysis engine, and is deployable on cloud platforms like **Vercel**.

---

## 🧭 Features

* 📊 Live intraday stock data (via Yahoo Finance)
* 🧠 Technical indicators:

  * RSI
  * MACD
  * VWAP
  * Bollinger Bands
  * EMA, ATR, and more
* 🔔 BUY / SELL / HOLD signal generation
* 💬 Sends alerts via Telegram (custom token + chat ID)
* 🌐 Streamlit dashboard
* ☁️ Deploy to Vercel, Render, or your own server

---

## 📦 Folder Structure

```
botfolio/
├── app.py               # Streamlit dashboard (UI)
├── bot4.py              # Signal generation logic
├── tickers_list.csv     # Stock tickers + names
├── requirements.txt     # Dependencies
├── README.md            # This file
```

---

## 🔧 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/botfolio.git
cd botfolio
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare Ticker List

Make sure your `tickers_list.csv` looks like this:

```csv
NAME,TICKER
Infosys,INFY.NS
TCS,TCS.NS
Reliance,RELIANCE.NS
```

### 4. Run the App

```bash
streamlit run app.py
```

* Enter your **Telegram Bot Token** and **Chat ID** in the UI
* Select stocks from the dropdown
* Click **Start Monitoring**
* Signals will be calculated and sent every hour

---

## 🛜 Deploying to Vercel

You can host the app with **Vercel**:

1. Push your code to GitHub
2. Import the repo into [vercel.com](https://vercel.com/)
3. Set the following **environment variables** in your Vercel project settings:

   * `TELEGRAM_BOT_TOKEN`
   * `TELEGRAM_CHAT_ID`
4. (Optional) Use a CRON job (e.g., [cron-job.org](https://cron-job.org/) or GitHub Actions) to call the signal logic (`bot4.py`) every hour

> You can split the backend into a CRON-triggered worker (just `bot4.py`) and keep the frontend on Streamlit.

---

## 🧪 Example Telegram Signal

```
BUY signal for INFY at ₹1583.20
SELL signal for TCS at ₹3835.90
```

Delivered straight to your Telegram inbox 📬

---

## 🧰 Tech Stack

* [Python 3.9+](https://www.python.org/)
* [Streamlit](https://streamlit.io/)
* [yfinance](https://pypi.org/project/yfinance/)
* [pandas](https://pandas.pydata.org/)
* [Telegram Bot API](https://core.telegram.org/bots)

---

## ⚠️ Disclaimer

> Botfolio is a personal side project for educational purposes only.
> It is **not** financial advice.
> Use at your own risk. Don’t sue the bot if it tells you to YOLO into a loss.

---

## 👨‍💻 Author

Made with 💻 by [Sangharsh](https://github.com/Sangharsh1215)
Helping apes trade smarter 🦍💸

---

## 🌟 Like This?

Star the repo ⭐
Fork it 🍴
Or just flex it to your friends.



