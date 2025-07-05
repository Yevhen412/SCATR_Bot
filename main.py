import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, COMMISSION, TAKE_PROFIT_USD, STOP_LOSS_USD, MIN_SPREAD_PCT
from telegram_utils import send_telegram_message

entry_prices = {}
trades = {}

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "topic" not in data or "data" not in data:
            return

        topic = data["topic"]
        symbol = topic.split(".")[-1]
        orderbook = data["data"]

        bid = float(orderbook["b"][0][0])
        ask = float(orderbook["a"][0][0])
        spread = ask - bid

        spread_pct = spread / ask
        net_profit_per_unit = spread - 2 * COMMISSION * ask
        net_profit_total = net_profit_per_unit * TRADE_AMOUNT_USD

        # Условие на вход
        if symbol not in entry_prices and spread_pct > MIN_SPREAD_PCT and net_profit_total >= TAKE_PROFIT_USD:
            entry_prices[symbol] = ask
            t = time.strftime('%H:%M:%S')
            trades.setdefault(symbol, []).append((t, ask))
            send_telegram_message(f"🟢 [{symbol}] BUY @ {ask:.4f} | Время: {t}")

        # Условие на выход
        elif symbol in entry_prices:
            entry = entry_prices[symbol]
            profit = (bid - entry) * TRADE_AMOUNT_USD - 2 * COMMISSION * bid * TRADE_AMOUNT_USD

            if profit <= -STOP_LOSS_USD:
                send_telegram_message(f"🛑 [{symbol}] Стоп-лосс! SELL @ {bid:.4f} | Убыток: {profit:.2f} USDT")
                del entry_prices[symbol]

            elif profit >= TAKE_PROFIT_USD:
                send_telegram_message(f"✅ [{symbol}] Тейк-профит! SELL @ {bid:.4f} | Профит: {profit:.2f} USDT")
                del entry_prices[symbol]

    except Exception as e:
        send_telegram_message(f"❌ Ошибка обработки: {e}")

def on_open(ws):
    for symbol in SYMBOLS:
        ws.send(json.dumps({
            "op": "subscribe",
            "args": [f"orderbook.1.{symbol}"]
        }))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        for symbol, history in trades.items():
            if history:
                msg = f"📊 [{symbol}] Сводка за час:\n"
                for t, p in history:
                    msg += f"{t}: BUY @ {p:.2f}\n"
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
