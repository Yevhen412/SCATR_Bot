
import time
import threading
from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message
import websocket
import json

entry_prices = {symbol: None for symbol in SYMBOLS}
trades = {symbol: [] for symbol in SYMBOLS}


def on_message(ws, message, symbol):
    try:
        data = json.loads(message)
        if "data" in data and isinstance(data["data"], list):
            update = data["data"][0]
            bid = float(update["b"])
            ask = float(update["a"])
            spread = ask - bid
            gross_profit = spread
            net_profit = gross_profit - COMMISSION

            print(f"[{symbol}] BID: {bid}, ASK: {ask}, SPREAD: {spread:.4f}")
            print(f"[{symbol}] Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")

            entry_price = entry_prices.get(symbol)

            if entry_price and (bid < entry_price * 0.985):
                send_telegram_message(f"🔻 [{symbol}] Цена упала более чем на 1.5% — сделка не будет открыта.")
                return

            if entry_price and (bid < entry_price * 0.993):
                send_telegram_message(f"🛑 [{symbol}] Стоп-лосс: BID = {bid}")
                entry_prices[symbol] = None
                return

            if net_profit > 0.01:
                entry_prices[symbol] = ask
                trade_time = time.strftime('%H:%M:%S')
                trades[symbol].append((trade_time, ask))
                send_telegram_message(f"🟢 [{symbol}] BUY @ {ask:.2f}")
    except Exception as e:
        send_telegram_message(f"❌ [{symbol}] Ошибка обработки данных: {e}")


def on_open(ws, symbol):
    ws.send(json.dumps({
        "op": "subscribe",
        "args": [f"orderbook.1.{symbol}"]
    }))
    send_telegram_message(f"🤖 [{symbol}] Бот подключён к стакану и запущен.")


def start_socket(symbol):
    ws = websocket.WebSocketApp(
        "wss://stream.bybit.com/v5/public/spot",
        on_open=lambda ws: on_open(ws, symbol),
        on_message=lambda ws, msg: on_message(ws, msg, symbol)
    )
    ws.run_forever()


def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")


def summary():
    while True:
        time.sleep(3600)
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg = f"📊 [{symbol}] Сводка по сделкам за час:\n"
                for t, p in symbol_trades:
                    msg += f"{t}: BUY @ {p:.2f}\n"
                send_telegram_message(msg)
                trades[symbol].clear()


def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    for symbol in SYMBOLS:
        threading.Thread(target=start_socket, args=(symbol,), daemon=True).start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    run_bot()

