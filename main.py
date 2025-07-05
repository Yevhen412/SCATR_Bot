import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, COMMISSION
from telegram_utils import send_telegram_message

entry_prices = {}
entry_times = {}
trades = {}
wins = {}
losses = {}

recent_prices = {}

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "data" not in data or not isinstance(data["data"], list):
            return

        update = data["data"][0]
        symbol = update.get("s")
        bids = update.get("b")
        asks = update.get("a")

        if not symbol or not bids or not asks:
            return

        bid = float(bids[0][0])
        ask = float(asks[0][0])
        spread = ask - bid
        gross_profit = spread * TRADE_AMOUNT_USD / ask
        net_profit = gross_profit - (COMMISSION * 2 * TRADE_AMOUNT_USD)

        now = time.time()
        price_now = (bid + ask) / 2

        # Инициализация массива истории
        if symbol not in recent_prices:
            recent_prices[symbol] = []
        recent_prices[symbol].append((now, price_now))

        # Оставляем только последние 5 секунд
        recent_prices[symbol] = [
            (t, p) for (t, p) in recent_prices[symbol] if now - t <= 5
        ]

        if len(recent_prices[symbol]) >= 2:
            price_then = recent_prices[symbol][0][1]
            delta = abs(price_now - price_then) / price_then
            if delta > 0.003:
                print(f"🚫 {symbol}: Резкое изменение цены > 0.3%, сделка отменена.")
                return

        # Если уже в позиции, проверяем условия выхода
        if symbol in entry_prices:
            entry_price = entry_prices[symbol]
            profit = (bid - entry_price) * TRADE_AMOUNT_USD - (COMMISSION * 2 * TRADE_AMOUNT_USD)

            if profit >= 0.03:
                send_telegram_message(
                    f"✅ TP | {symbol}\n"
                    f"BUY @ {entry_price:.4f} → SELL @ {bid:.4f}\n"
                    f"💰 PnL: +{profit:.4f} USDT"
                )
                wins[symbol] = wins.get(symbol, 0) + 1
                trades[symbol].append((time.strftime('%H:%M:%S'), profit))
                del entry_prices[symbol]
                del entry_times[symbol]

            elif profit <= -0.015:
                send_telegram_message(
                    f"🛑 SL | {symbol}\n"
                    f"BUY @ {entry_price:.4f} → SELL @ {bid:.4f}\n"
                    f"💸 PnL: {profit:.4f} USDT"
                )
                losses[symbol] = losses.get(symbol, 0) + 1
                trades[symbol].append((time.strftime('%H:%M:%S'), profit))
                del entry_prices[symbol]
                del entry_times[symbol]

        else:
            if spread / ask < 0.0002:
                return
            if net_profit >= 0.03:
                entry_prices[symbol] = ask
                entry_times[symbol] = now
                trades.setdefault(symbol, []).append((time.strftime('%H:%M:%S'), 0.0))
                send_telegram_message(f"🟢 BUY {symbol} @ {ask:.4f}")

    except Exception as e:
        print(f"❌ Ошибка в on_message: {e}")
        send_telegram_message(f"❌ Ошибка в on_message: {e}")

def on_open(ws):
    for symbol in SYMBOLS:
        ws.send(json.dumps({
            "op": "subscribe",
            "args": [f"orderbook.1.{symbol}"]
        }))
    send_telegram_message("🤖 Бот подключён и слушает стаканы...")

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        msg = "📊 Сводка за последний час:\n"
        for symbol in trades:
            deals = trades[symbol]
            w = wins.get(symbol, 0)
            l = losses.get(symbol, 0)
            if deals:
                msg += f"\n[{symbol}] — Сделок: {len(deals)}, ✅: {w}, ❌: {l}\n"
                for t, p in deals:
                    msg += f"{t} → {p:.4f} USDT\n"
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
            send_telegram_message(f"❌ Ошибка WebSocket: {e}")
            time.sleep(10)

# 🔁 Точка входа
if __name__ == "__main__":
    run_bot()
