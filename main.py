import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message

entry_prices = {}
trades = {}

def on_message(ws, message):
    print("👀 Вошёл в on_message")
    print("🔹 Сообщение:", message)

    data = json.loads(message)

    try:
        data = json.loads(message)
        if "data" in data and isinstance(data["data"], list):
            update = data["data"][0]
            bid = float(update["b"][0][0])
            ask = float(update["a"][0][0])
            spread = ask - bid
            gross_profit = spread
            net_profit = gross_profit - COMMISSION

            print(f"BID: {bid}, ASK: {ask}, SPREAD: {spread:.4f}")
            print(f"Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")

            # Защита от падения
            if entry_price and (bid < entry_price * 0.985):
                send_telegram_message("🔻 Цена упала более чем на 1.5% — сделка не будет открыта.")
                return

            # Стоп-лосс
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

            # Стоп-лосс
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

            # Стоп-лосс
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
    print("🧩 Внутри on_open")
    args = [f"orderbook.1.{symbol}" for symbol in SYMBOLS]
    ws.send(json.dumps({
        "op": "subscribe",
        "args": args
    }))
    for symbol in SYMBOLS:
        send_telegram_message(f"🤖 [{symbol}] Бот подключён к стакану и запущен.")

def heartbeat():
    while True:
        time.sleep(600)
        print("💓 Heartbeat: бот активен")
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        print("📝 Сводка формируется")
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg = f"📊 [{symbol}] Сводка за час:\n"
                for t, p in symbol_trades:
                    msg += f"{t}: BUY @ {p:.2f}\n"
                send_telegram_message(msg)
        trades.clear()

def run_bot():
    print("⚙️ run_bot() запускается")
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    while True:
        try:
            print("🔌 Подключение к WebSocket...")
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message
            )
            print("🟢 WebSocket создан, запускаем run_forever()")
            ws.run_forever()
        except Exception as e:
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            print(f"❌ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 main.py стартует")
    run_bot()
