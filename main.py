
import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message

trades = {}
entry_prices = {}

def on_message(symbol):
    def inner(ws, message):
        global trades, entry_prices

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

                # Фильтр резкого падения
                if entry_price and bid < entry_price * 0.985:
                    send_telegram_message(f"🔻 [{symbol}] Цена упала > 1.5% — сделка не открыта.")
                    return

                # Стоп-лосс
                if entry_price and bid < entry_price * 0.993:
                    send_telegram_message(f"🛑 [{symbol}] Стоп-лосс: BID = {bid:.2f}")
                    entry_prices[symbol] = None
                    return

                # Сделка
                if net_profit > 0.01:
                    entry_prices[symbol] = ask
                    trade_time = time.strftime('%H:%M:%S')
                    trades.setdefault(symbol, []).append((trade_time, ask))
                    send_telegram_message(f"🟢 [{symbol}] BUY @ {ask:.2f}")
        except Exception as e:
            send_telegram_message(f"❌ [{symbol}] Ошибка: {e}")
    return inner

def on_open(symbol):
    def inner(ws):
        ws.send(json.dumps({
            "op": "subscribe",
            "args": [f"orderbook.1.{symbol}"]
        }))
        send_telegram_message(f"🤖 [{symbol}] Бот подключён к стакану и запущен.")
    return inner

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg = f"📊 [{symbol}] Сводка за час:\n"
                for t, p in symbol_trades:
                    msg += f"{t}: BUY @ {p:.2f}\n"
                send_telegram_message(msg)
                trades[symbol] = []

import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message

trades = {}
entry_prices = {}

def on_message(ws, message, symbol):
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

            print(f"[{symbol}] BID: {bid}, ASK: {ask}, SPREAD: {spread:.4f}")
            print(f"[{symbol}] Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")


                entry_price = entry_prices.get(symbol)

                # Фильтр резкого падения
                if entry_price and bid < entry_price * 0.985:
                    send_telegram_message(f"🔻 [{symbol}] Цена упала > 1.5% — сделка не открыта.")
                    return

                # Стоп-лосс
                if entry_price and bid < entry_price * 0.993:
                    send_telegram_message(f"🛑 [{symbol}] Стоп-лосс: BID = {bid:.2f}")
                    entry_prices[symbol] = None
                    return

                # Сделка
                if net_profit > 0.01:
                    entry_prices[symbol] = ask
                    trade_time = time.strftime('%H:%M:%S')
                    trades.setdefault(symbol, []).append((trade_time, ask))
                    send_telegram_message(f"🟢 [{symbol}] BUY @ {ask:.2f}")
        except Exception as e:
            send_telegram_message(f"❌ [{symbol}] Ошибка: {e}")
    return inner

def on_open(symbol):
    def inner(ws):
        ws.send(json.dumps({
            "op": "subscribe",
            "args": [f"orderbook.1.{symbol}"]
        }))
        send_telegram_message(f"🤖 [{symbol}] Бот подключён к стакану и запущен.")
    return inner

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg = f"📊 [{symbol}] Сводка за час:\n"
                for t, p in symbol_trades:
                    msg += f"{t}: BUY @ {p:.2f}\n"
                send_telegram_message(msg)
                trades[symbol] = []

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    def start_stream(symbol):
        def on_msg(ws, message):
            on_message(ws, message, symbol)

        def on_open_wrapper(ws):
            ws.send(json.dumps({
                "op": "subscribe",
                "args": [f"orderbook.1.{symbol}"]
            }))
            send_telegram_message(f"🤖 [{symbol}] Бот подключён к стакану и запущен.")

        while True:
            try:
                ws = websocket.WebSocketApp(
                    "wss://stream.bybit.com/v5/public/spot",
                    on_open=on_open_wrapper,
                    on_message=on_msg
                )
                ws.run_forever()
            except Exception as e:
                send_telegram_message(f"❌ [{symbol}] Ошибка подключения: {e}")
                time.sleep(5)

    for symbol in SYMBOLS:
        threading.Thread(target=start_stream, args=(symbol,), daemon=True).start()

    while True:
        time.sleep(1)

