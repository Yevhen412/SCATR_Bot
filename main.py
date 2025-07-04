
import time
import threading
from config import SYMBOL, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message
import websocket
import json

last_price = None
entry_price = None
trade_time = None
trades = []

def on_message(ws, message):
    global last_price, entry_price, trade_time, trades

    try:
        data = json.loads(message)
        if "data" in data and isinstance(data["data"], list):
            update = data["data"][0]
            bid = float(update["b"])
            ask = float(update["a"])
            spread = ask - bid
            gross_profit = spread
            net_profit = gross_profit - COMMISSION

            print(f"BID: {bid}, ASK: {ask}, SPREAD: {spread:.4f}")
            print(f"Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")

            # Защита от падения
            if entry_price and (bid < entry_price * 0.985):
                send_telegram_message("🔻 Цена упала более чем на 1.5% — сделка не будет открыта.")
                return

            # Выход по стоп-лоссу
            if entry_price and (bid < entry_price * 0.993):
                send_telegram_message(f"🛑 Стоп-лосс: BID = {bid}")
                entry_price = None
                return

            if net_profit > 0.01:
                entry_price = ask
                trade_time = time.strftime('%H:%M:%S')
                trades.append((trade_time, ask))
                send_telegram_message(f"🟢 BUY @ {ask:.2f}")
    except Exception as e:
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")

def on_open(ws):
    ws.send(json.dumps({
        "op": "subscribe",
        "args": [f"orderbook.1.{SYMBOL}"]
    }))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        if trades:
            msg = "📊 Сводка по сделкам за час:
"
            for t, p in trades:
                msg += f"{t}: BUY @ {p:.2f}
"
            send_telegram_message(msg)
            trades.clear()

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
