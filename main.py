
import json
import websocket
import threading
from config import TRADE_AMOUNT_USD, SYMBOL
from telegram_utils import send_telegram_message

position = None
entry_price = 0

def on_message(ws, message):
    global position, entry_price
    data = json.loads(message)

    if "data" not in data:
        return

    bids = data['data']['b']
    asks = data['data']['a']

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    spread = best_ask - best_bid

    if position is None and spread > 0.2:
        position = "long"
        entry_price = best_ask
        send_telegram_message(f"🟢 BUY @ {entry_price:.2f}")

    elif position == "long":
        exit_price = best_bid
        profit = (exit_price - entry_price) * (TRADE_AMOUNT_USD / entry_price)

        if abs(profit) >= 0.1:
            send_telegram_message(f"🔴 SELL @ {exit_price:.2f}\n💰 PnL: {profit:.2f} USDT")
            position = None

def on_open(ws):
    ws.send(json.dumps({
        "op": "subscribe",
        "args": [f"orderbook.1.{SYMBOL}"]
    }))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

def run_bot():
    ws = websocket.WebSocketApp("wss://stream.bybit.com/v5/public/spot",
                                on_open=on_open,
                                on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.start()
