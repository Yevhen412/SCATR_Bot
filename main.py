
import json
import websocket
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

    print(f"📩 Получено сообщение от WebSocket")
    print(f"💹 best_bid: {best_bid}, best_ask: {best_ask}, spread: {spread}")

    # Комиссия Bybit: например, 0.1% вход + 0.1% выход = 0.2%
    estimated_fee = 0.002  
    exit_price = best_bid
    profit = (exit_price - entry_price) * (TRADE_AMOUNT_USD / entry_price) if position else 0
    net_profit = profit - (TRADE_AMOUNT_USD * estimated_fee)

    if position is None and spread > 0.2:
        position = "long"
        entry_price = best_ask
        send_telegram_message(f"🟢 BUY @ {entry_price:.2f}")
        print(f"🟢 BUY @ {entry_price:.2f}")

    elif position == "long":
        if net_profit >= 0.1:
            send_telegram_message(f"🔴 SELL @ {exit_price:.2f}\n💰 PnL: {net_profit:.2f} USDT (after fee)")
            print(f"🔴 SELL @ {exit_price:.2f}, Net PnL: {net_profit:.2f} USDT")
            position = None
        else:
            print(f"Проверка выхода: exit @ {exit_price}, profit = {profit:.2f}, net = {net_profit:.2f}")

def on_open(ws):
    ws.send(json.dumps({
        "op": "subscribe",
        "args": [f"orderbook.1.{SYMBOL}"]
    }))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")
    print("✅ Подписка на WebSocket отправлена.")

def run_bot():
    ws = websocket.WebSocketApp("wss://stream.bybit.com/v5/public/spot",
                                on_open=on_open,
                                on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    run_bot()
