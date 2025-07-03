
import time
import threading
import json
from websocket import WebSocketApp
from telegram_utils import send_telegram_message
from config import TRADE_AMOUNT_USD, SYMBOL, COMMISSION

position = None
entry_price = 0

def on_open(ws):
    print("🔌 WebSocket соединение открыто")
    subscribe_message = {
        "op": "subscribe",
        "args": [f"orderbook.1.{SYMBOL}"]
    }
    ws.send(json.dumps(subscribe_message))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

def on_message(ws, message):
    global position, entry_price
    try:
        data = json.loads(message)
        if "data" in data:
            orderbook = data["data"]
            best_bid = float(orderbook["b"][0][0])
            best_ask = float(orderbook["a"][0][0])
            spread = best_ask - best_bid

            print(f"🔍 BID: {best_bid}, ASK: {best_ask}, SPREAD: {spread:.4f}")

            # Открытие позиции
            if position is None and spread > 0.2:
                entry_price = best_ask
                position = "long"
                send_telegram_message(f"🟢 BUY @ {entry_price:.2f}")

            # Закрытие позиции
            elif position == "long":
                exit_price = best_bid
                gross_profit = (exit_price - entry_price) * (TRADE_AMOUNT_USD / entry_price)
                commission_cost = TRADE_AMOUNT_USD * (COMMISSION / 100)
                net_profit = gross_profit - commission_cost

                print(f"💡 Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")

                if net_profit >= 0.1:
                    send_telegram_message(f"🔴 SELL @ {exit_price:.2f}\n💰 Net PnL: {net_profit:.2f} USDT")
                    position = None

    except Exception as e:
        print(f"❌ Ошибка обработки данных: {e}")
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")

def heartbeat():
    while True:
        time.sleep(600)  # 10 минут
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
