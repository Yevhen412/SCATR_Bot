
import json
import websocket
import threading
import time
from config import TRADE_AMOUNT_USD, SYMBOL, COMMISSION
from telegram_utils import send_telegram_message

position = None
entry_price = 0

def on_message(ws, message):
    global position, entry_price
    try:
        data = json.loads(message)

        if "data" not in data:
            return

        bids = data['data']['b']
        asks = data['data']['a']

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid

        print(f"📈 best_bid: {best_bid}, best_ask: {best_ask}, spread: {spread}")

        if position is None and spread > 0.1:
            entry_price = best_ask
            cost = TRADE_AMOUNT_USD
            fee = entry_price * (TAKER_FEE / 100)
            position = "long"
            send_telegram_message(f"🟢 BUY @ {entry_price:.2f}")
        
        elif position == "long":
            exit_price = best_bid
            gross_profit = (exit_price - entry_price) * (TRADE_AMOUNT_USD / entry_price)
            entry_fee = entry_price * (TAKER_FEE / 100)
            exit_fee = exit_price * (MAKER_FEE / 100)
            net_profit = gross_profit - entry_fee - exit_fee

            print(f"Проверка выхода: exit @ {exit_price}, gross = {gross_profit:.2f}, net = {net_profit:.2f}")

            if net_profit >= 0.1:
                send_telegram_message(f"🔴 SELL @ {exit_price:.2f}\n💰 Net PnL: {net_profit:.2f} USDT")
                position = None
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

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()

    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            send_telegram_message(f"⚠️ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()

