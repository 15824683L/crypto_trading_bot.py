import time
import requests
import pandas as pd
import ccxt
from datetime import datetime
import traceback
from keep_alive import keep_alive
keep_alive()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7615583534:AAHaKfWLN7NP83LdmR32i6BfNWqq73nBsAE"
TELEGRAM_CHAT_ID = "8191014589"
TELEGRAM_GROUP_CHAT_ID = "@TradeAlertcrypto"

# MEXC API Setup (Binance Alternative)
exchange = ccxt.mexc({
    'enableRateLimit': True,
    'session': requests.Session(),
})



active_trades = {}
last_signal_time = time.time()

# Function to Send Telegram Message
def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# Fetch OHLCV Data
def fetch_data(symbol, interval, lookback):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    df = df.astype(float)
    return df

# Strategy: Liquidity Grab + Order Block
def liquidity_grab_order_block(df):
    df['high_shift'] = df['high'].shift(1)
    df['low_shift'] = df['low'].shift(1)
    liquidity_grab = (df['high'] > df['high_shift']) & (df['low'] < df['low_shift'])
    order_block = df['close'] > df['open']

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


# Function to Check TP or SL Hit
def check_tp_sl():
    global active_trades
    for pair, trade in list(active_trades.items()):
        df = fetch_data(pair, "1m")
        time.sleep(1)
        if df is not None:
            last_price = df['close'].iloc[-1]
            now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            signal_time = trade.get("signal_time", "N/A")

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

# Main Trading Loop

CRYPTO_SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"]
timeframes = {
    "Intraday 15m": '15m',
    "Intraday 30m": '30m',
    "Swing": '1h',
    "Position": '1d'
}
active_trades = {}
last_signal_time = time.time()

while True:
    signal_found = False

    for symbol in CRYPTO_SYMBOLS:
        if symbol in active_trades:
            df = fetch_data(symbol, Client.KLINE_INTERVAL_15MINUTE, "2 days ago UTC")
            if df is not None and not df.empty:
                last_price = df['close'].iloc[-1]
                trade = active_trades[symbol]
                now_time = datetime.now().strftime('%Y-%m-%d %H:%M')

                if trade['direction'] == "BUY":
                    if last_price >= trade['tp']:
                        print(f"✅ TP HIT for {symbol} at {now_time} Price: {last_price}")
                        del active_trades[symbol]
                    elif last_price <= trade['sl']:
                        print(f"🛑 SL HIT for {symbol} at {now_time} Price: {last_price}")
                        del active_trades[symbol]

                elif trade['direction'] == "SELL":
                    if last_price <= trade['tp']:
                        print(f"✅ TP HIT for {symbol} at {now_time} Price: {last_price}")
                        del active_trades[symbol]
                    elif last_price >= trade['sl']:
                        print(f"🛑 SL HIT for {symbol} at {now_time} Price: {last_price}")
                        del active_trades[symbol]
            continue

        for label, tf in timeframes.items():
            df = fetch_data(symbol, tf, "2 days ago UTC")
            if df is not None and not df.empty:
                signal, entry, sl, tp, tsl, emoji = liquidity_grab_order_block(df)
                if signal != "NO SIGNAL":
                    signal_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    msg = (
                        f"{emoji} {signal} Signal for {symbol}\n"
                        f"Type: {label}\nTimeframe: {tf}\nTime: {signal_time}\n"
                        f"Entry: {entry}\nSL: {sl}\nTP: {tp}\nTSL: {tsl}"
                    )
                    print(msg)

                    active_trades[symbol] = {
                        "signal_time": signal_time,
                        "entry": entry,
                        "sl": sl,
                        "tp": tp,
                        "direction": signal
                    }
                    signal_found = True
                    break
        if signal_found:
            break

    if not signal_found and (time.time() - last_signal_time > 3600):
        print("⚠️ No Signal in the Last 1 Hour (Crypto Pairs)")
        last_signal_time = time.time()

    time.sleep(60)
    print("Bot is running 24/7!")
