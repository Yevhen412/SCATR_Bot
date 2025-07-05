import time
import threading
import json
import websocket

from config import SYMBOLS, TRADE_AMOUNT_USD, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COMMISSION
from telegram_utils import send_telegram_message

entry_prices = {}
trades = []
statistics = {}

def enter_trade(symbol, price, now):
    trades = []
    trade = {
        "symbol": symbol,
        "entry_price": price,
        "entry_time": now,
        "status": "open"
    }

    if symbol not in trades:
        trades[symbol] = []  # создаём список для нового символа

    trades[symbol].append(trade)

    send_telegram_message(
        f"📥 Вход в сделку по {symbol}\nЦена входа: {price}\nВремя: {now}"
    )

def exit_trade(symbol, price, now):
    if symbol not in trades:
        return  # нет активных сделок для символа

    for trade in trades[symbol]:
        if trade["status"] == "open":
            trade["exit_price"] = price
            trade["exit_time"] = now
            trade["profit"] = round(price - trade["entry_price"], 6)
            trade["status"] = "closed"

            update_statistics(symbol, trade["profit"])

            send_telegram_message(
                f"📤 Выход из сделки по {symbol}\n"
                f"Цена выхода: {price}\n"
                f"Прибыль: {trade['profit']}\n"
                f"Время: {now}"
            )
            break

def update_statistics(symbol, profit):
    if symbol not in statistics:
        statistics[symbol] = {"count": 0, "total_profit": 0.0}
    statistics[symbol]["count"] += 1
    statistics[symbol]["total_profit"] += profit

entry_prices = {}
trades = {}

def on_message(ws, message):
    print("📥 Вошёл в on_message")

    try:
        data = json.loads(message)

        # Быстрая проверка на наличие orderbook обновления
        if "topic" not in data or "data" not in data:
            return

        update = data["data"]
        if not isinstance(update, dict) or "b" not in update or "a" not in update:
            raise ValueError("Неверный формат данных")

        topic = data.get("topic", "")
        symbol = topic.split(".")[-1] if "." in topic else "UNKNOWN"

        bid = float(update["b"][0][0])
        ask = float(update["a"][0][0])
        spread = ask - bid
        spread_pct = (spread / ask) * 100
        gross_profit = spread
        net_profit = gross_profit - COMMISSION

        print(f"BID: {bid}, ASK: {ask}, SPREAD: {spread:.4f} ({spread_pct:.4f}%)")
        print(f"Gross: {gross_profit:.4f}, Net: {net_profit:.4f}")

        now = time.strftime("%H:%M:%S")

        # 💡 Условие фиктивной сделки
        if spread_pct > 0.02:
            enter_trade(symbol, bid, now)

    except Exception as e:
        print(f"Ошибка обработки данных: {e}")
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")
def heartbeat():
    while True:
        time.sleep(600)
        print("💓 Heartbeat: бот активен")
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        print("📝 Сводка формируется")
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg = f"📊 [{symbol}] Сводка за час:\n"
                for t, p in symbol_trades:
                    msg += f"{t}: BUY @ {p:.2f}\n"
                send_telegram_message(msg)
        trades.clear()

def on_open(ws):
    print("🔌 Соединение открыто")
    try:
        args = [f"orderbook.1.{symbol}" for symbol in SYMBOLS]
        subscribe_message = {
            "op": "subscribe",
            "args": args
        }
        ws.send(json.dumps(subscribe_message))
        print(f"📡 Подписка отправлена: {args}")
        send_telegram_message(f"✅ Соединение открыто. Подписка отправлена: {args}")
    except Exception as e:
        print(f"❌ Ошибка при подписке: {e}")
        send_telegram_message(f"❌ Ошибка при подписке: {e}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Соединение закрыто")
    send_telegram_message("🔌 Соединение с WebSocket закрыто")

def on_error(ws, error):
    print(f"❌ Ошибка WebSocket: {error}")
    send_telegram_message(f"❌ Ошибка WebSocket: {error}")

def run_bot():
    print("⚙️ run_bot() запускается")
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    while True:
        try:
            print("🔌 Подключение к WebSocket...")
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            print("🟢 WebSocket создан, запускаем run_forever()")
            ws.run_forever()
        except Exception as e:
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            print(f"❌ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 main.py стартует")
    run_bot()
