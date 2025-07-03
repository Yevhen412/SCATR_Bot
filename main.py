
import time
import threading
import json
from websocket import WebSocketApp
from telegram_utils import send_telegram_message
from config import TRADE_AMOUNT_USD, SYMBOL, COMMISSION
def on_open(ws):
    print("🔌 WebSocket соединение открыто")
    subscribe_message = {
        "op": "subscribe",
        "args": [f"orderbook.1.{SYMBOL}"]
    }
    ws.send(json.dumps(subscribe_message))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

def on_message(ws, message):
    try:
        print(f"[WebSocket] Получено сообщение: {message}")
        data = json.loads(message)
        if "data" in data:
            orderbook = data["data"]
            best_bid = float(orderbook["b"][0][0])
            best_ask = float(orderbook["a"][0][0])
            spread = best_ask - best_bid
            profit = spread
            net_profit = profit - (best_bid * TAKER_FEE / 100) - (best_ask * MAKER_FEE / 100)

            print(f"🔍 BID: {best_bid}, ASK: {best_ask}, PROFIT: {profit:.2f}, NET: {net_profit:.2f}")

            if net_profit > 0:
                send_telegram_message(f"🟢 BUY @ {best_bid}")
    except Exception as e:
        print(f"❌ Ошибка обработки данных: {e}")
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")

def heartbeat():
    while True:
        time.sleep(600)
        print("✅ Heartbeat: бот активен")
        send_telegram_message("✅ Бот активен")

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    while True:
        try:
            ws = WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            print(f"❌ Ошибка WebSocket: {e}")
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
