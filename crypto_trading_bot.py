import time
import requests
import pandas as pd
import ccxt
from datetime import datetime
import traceback
from keep\_alive import keep\_alive

keep\_alive()

# Telegram Bot Configuration

TELEGRAM\_BOT\_TOKEN = "7615583534\:AAHaKfWLN7NP83LdmR32i6BfNWqq73nBsAE"
TELEGRAM\_CHAT\_ID = "8191014589"
TELEGRAM\_GROUP\_CHAT\_ID = "@TradeAlertcrypto"

# MEXC API Setup (Binance Alternative)

exchange = ccxt.mexc({
'enableRateLimit': True,
'session': requests.Session(),
})

# Function to Send Telegram Message

def send\_telegram\_message(message, chat\_id):
url = f"[https://api.telegram.org/bot{TELEGRAM\_BOT\_TOKEN}/sendMessage](https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage)"
data = {"chat\_id": chat\_id, "text": message, "parse\_mode": "Markdown"}
try:
requests.post(url, data=data)
except Exception as e:
print("Telegram Error:", e)

# Fetch OHLCV Data

def fetch\_data(symbol, interval, lookback):
since = exchange.parse8601(lookback)
ohlcv = exchange.fetch\_ohlcv(symbol, interval, since=since)
df = pd.DataFrame(ohlcv, columns=[
'timestamp', 'open', 'high', 'low', 'close', 'volume'
])
df['timestamp'] = pd.to\_datetime(df['timestamp'], unit='ms')
df.set\_index('timestamp', inplace=True)
df = df.astype(float)
return df

# Strategy: Liquidity Grab + Order Block

def liquidity\_grab\_order\_block(df):
df['high\_shift'] = df['high'].shift(1)
df['low\_shift'] = df['low'].shift(1)
liquidity\_grab = (df['high'] > df['high\_shift']) & (df['low'] < df['low\_shift'])
order\_block = df['close'] > df['open']

```
if liquidity_grab.iloc[-1] and order_block.iloc[-1]:
    entry = round(df['close'].iloc[-1], 2)
    sl = round(df['low'].iloc[-2], 2)
    tp = round(entry + (entry - sl) * 2, 2)
    tsl = round(entry + (entry - sl) * 1.5, 2)
    return "BUY", entry, sl, tp, tsl, "\U0001F7E2"
elif liquidity_grab.iloc[-1] and not order_block.iloc[-1]:
    entry = round(df['close'].iloc[-1], 2)
    sl = round(df['high'].iloc[-2], 2)
    tp = round(entry - (sl - entry) * 2, 2)
    tsl = round(entry - (sl - entry) * 1.5, 2)
    return "SELL", entry, sl, tp, tsl, "\U0001F534"
return "NO SIGNAL", None, None, None, None, None
```

# Function to Check TP or SL Hit

def check\_tp\_sl():
global active\_trades
for pair, trade in list(active\_trades.items()):
df = fetch\_data(pair, '1m', '2 days ago UTC')
if df is not None:
last\_price = df['close'].iloc[-1]
now\_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
signal\_time = trade.get("signal\_time", "N/A")

```
        if trade['direction'] == "BUY":
            if last_price >= trade['tp']:
                msg = (
                    f"✅ *{pair} TP Hit!*\n📈 Direction: BUY\n🎯 Entry: `{trade['entry']}`\n"
                    f"💰 TP: `{trade['tp']}`\n🕐 Signal Time: `{signal_time}`\n📍 TP Time: `{now_time}`"
                )
                send_telegram_message(msg, TELEGRAM_CHAT_ID)
                send_telegram_message(msg, TELEGRAM_GROUP_CHAT_ID)
                del active_trades[pair]
            elif last_price <= trade['sl']:
                msg = (
                    f"❌ *{pair} SL Hit!*\n📈 Direction: BUY\n🎯 Entry: `{trade['entry']}`\n"
                    f"💥 SL: `{trade['sl']}`\n🕐 Signal Time: `{signal_time}`\n📍 SL Time: `{now_time}`"
                )
                send_telegram_message(msg, TELEGRAM_CHAT_ID)
                send_telegram_message(msg, TELEGRAM_GROUP_CHAT_ID)
                del active_trades[pair]

        elif trade['direction'] == "SELL":
            if last_price <= trade['tp']:
                msg = (
                    f"✅ *{pair} TP Hit!*\n📉 Direction: SELL\n🎯 Entry: `{trade['entry']}`\n"
                    f"💰 TP: `{trade['tp']}`\n🕐 Signal Time: `{signal_time}`\n📍 TP Time: `{now_time}`"
                )
                send_telegram_message(msg, TELEGRAM_CHAT_ID)
                send_telegram_message(msg, TELEGRAM_GROUP_CHAT_ID)
                del active_trades[pair]
            elif last_price >= trade['sl']:
                msg = (
                    f"❌ *{pair} SL Hit!*\n📉 Direction: SELL\n🎯 Entry: `{trade['entry']}`\n"
                    f"💥 SL: `{trade['sl']}`\n🕐 Signal Time: `{signal_time}`\n📍 SL Time: `{now_time}`"
                )
                send_telegram_message(msg, TELEGRAM_CHAT_ID)
                send_telegram_message(msg, TELEGRAM_GROUP_CHAT_ID)
                del active_trades[pair]
```

# Main Trading Loop

CRYPTO\_SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"]
timeframes = {
"Intraday 15m": '15m',
"Intraday 30m": '30m',
"Swing": '1h',
"Position": '1d'
}

active\_trades = {}
last\_signal\_time = time.time()

while True:
signal\_found = False

```
for symbol in CRYPTO_SYMBOLS:
    if symbol in active_trades:
        df = fetch_data(symbol,
```

::contentReference[oaicite:3]{index="3"}
                    # Fetch the new data
            df = fetch_data(symbol, '1m', '2 days ago UTC')

            if df is not None:
                signal, entry, sl, tp, tsl, color = liquidity_grab_order_block(df)

                # Checking for a valid signal and managing trades
                if signal != "NO SIGNAL" and symbol not in active_trades:
                    active_trades[symbol] = {
                        'direction': signal,
                        'entry': entry,
                        'sl': sl,
                        'tp': tp,
                        'tsl': tsl,
                        'signal_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    msg = (
                        f"⚡️ New {signal} Signal for {symbol}!\n"
                        f"🎯 Entry: `{entry}`\n"
                        f"💥 SL: `{sl}`\n"
                        f"💰 TP: `{tp}`\n"
                        f"🔺 TSL: `{tsl}`\n"
                        f"⏰ Signal Time: `{active_trades[symbol]['signal_time']}`"
                    )
                    send_telegram_message(msg, TELEGRAM_CHAT_ID)
                    send_telegram_message(msg, TELEGRAM_GROUP_CHAT_ID)
                    print(f"{signal} Signal Sent for {symbol} at {entry}")

                elif symbol in active_trades:
                    # Checking if the stop-loss or take-profit conditions are met
                    check_tp_sl()

    # Sleep for 1 minute before checking again
    time.sleep(60)
