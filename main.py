import time
import threading
import json
import websocket
from collections import deque

from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message
from volatility_analyzer import update_volatility, start_volatility_analysis

entry_prices = {}
trades = {}
price_history = {symbol: deque(maxlen=5) for symbol in SYMBOLS}  # Храним последние 5 тиков

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "topic" not in data or "data" not in data:
            return

        topic = data["topic"]
        symbol = topic.split(".")[-1]
        orderbook = data["data"]

        bid = float(orderbook['b'][0][0])
        ask = float(orderbook['a'][0][0])
        spread = ask - bid
        gross_profit = spread * TRADE_AMOUNT_USD / ask
        net_profit = gross_profit - (COMMISSION * 2 * TRADE_AMOUNT_USD)

        # ⚠️ Фильтр от "ловли ножей": если цена изменилась > 1% за 5 тиков
        price_history[symbol].append((bid + ask) / 2)
        if len(price_history[symbol]) == 5:
            old_price = price_history[symbol][0]
            new_price = price_history[symbol][-1]
            delta = abs(new_price - old_price) / old_price
            if delta > 0.01:
                print(f"⚠️ Резкое движение по {symbol}, фильтр активирован: Δ={delta:.4f}")
                return

        # 📈 Обновление волатильности
        mid_price = (bid + ask) / 2
        update_volatility(symbol, mid_price)

        # ✅ Вход только при чистой прибыли > 0.005 USDT
        if net_profit > 0.005:
            entry_price = ask
            exit_price = bid
            profit = net_profit
            timestamp = time.strftime('%H:%M:%S')
            trades.setdefault(symbol, []).append((timestamp, profit))

            send_telegram_message(
                f"🟢 BUY {symbol} @ {entry_price:.4f}\n"
                f"🔴 SELL {symbol} @ {exit_price:.4f}\n"
                f"💰 Net Profit: {profit:.4f} USDT"
            )

    except Exception as e:
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")

def on_open(ws):
    args = [f"orderbook.1.{symbol}" for symbol in SYMBOLS]
    ws.send(json.dumps({"op": "subscribe", "args": args}))
    send_telegram_message("🤖 Бот подключён к стакану и запущен.")

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
                    msg += f"{t}: PnL = {p:.4f} USDT\n"
                send_telegram_message(msg)
        trades.clear()

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()
    start_volatility_analysis()

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
