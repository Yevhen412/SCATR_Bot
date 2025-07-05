import time
import threading
import json
import websocket
from config import SYMBOLS, TRADE_AMOUNT_USD, COMMISSION
from telegram_utils import send_telegram_message

entry_prices = {}
trade_times = {}
trades = {symbol: [] for symbol in SYMBOLS}

def on_message(ws, message):
    print("📥 Получено сообщение от WebSocket")
    try:
        data = json.loads(message)

        if "data" in data and isinstance(data["data"], list):
            for update in data["data"]:
                if "s" not in update or "b" not in update or "a" not in update:
                    continue

                symbol = update["s"]
                bid_list = update["b"]
                ask_list = update["a"]

                if not bid_list or not ask_list:
                    continue

                best_bid = float(bid_list[0][0])
                best_ask = float(ask_list[0][0])
                spread = best_bid - best_ask
                expected_profit = spread - (best_ask * COMMISSION * 2)
                usd_profit = expected_profit * (TRADE_AMOUNT_USD / best_ask)

                print(f"{symbol} | BID: {best_bid:.4f} | ASK: {best_ask:.4f} | Net: {usd_profit:.5f}")

                if symbol not in entry_prices and usd_profit >= 0.03:
                    entry_prices[symbol] = best_ask
                    trade_times[symbol] = time.strftime('%H:%M:%S')
                    trades[symbol].append((trade_times[symbol], best_ask))
                    send_telegram_message(f"🟢 [{symbol}] BUY @ {best_ask:.4f}")

                elif symbol in entry_prices:
                    entry = entry_prices[symbol]
                    pnl = (best_bid - entry) * (TRADE_AMOUNT_USD / entry)

                    if pnl >= 0.03:
                        send_telegram_message(f"🔴 [{symbol}] SELL @ {best_bid:.4f}\n💰 PnL: {pnl:.4f} USDT")
                        del entry_prices[symbol]
                        del trade_times[symbol]

                    elif best_bid < entry * (1 - 0.007):  # стоп-лосс 0.7%
                        loss = (best_bid - entry) * (TRADE_AMOUNT_USD / entry)
                        send_telegram_message(f"🛑 [{symbol}] STOP-LOSS @ {best_bid:.4f}\n💸 Loss: {loss:.4f} USDT")
                        del entry_prices[symbol]
                        del trade_times[symbol]

    except Exception as e:
        print(f"Ошибка обработки данных: {e}")
        send_telegram_message(f"❌ Ошибка обработки данных: {e}")

def on_open(ws):
    print("🔌 WebSocket соединение открыто")
    args = [f"orderbook.1.{symbol}" for symbol in SYMBOLS]
    ws.send(json.dumps({
        "op": "subscribe",
        "args": args
    }))
    send_telegram_message("🤖 Бот запущен и подписан на стаканы.")

def on_error(ws, error):
    print(f"❌ WebSocket ошибка: {error}")
    send_telegram_message(f"❌ WebSocket ошибка: {error}")

def on_close(ws):
    print("🔌 WebSocket соединение закрыто")
    send_telegram_message("⚠️ Соединение закрыто, попытка переподключения...")

def heartbeat():
    while True:
        time.sleep(600)
        send_telegram_message("✅ Бот активен")

def summary():
    while True:
        time.sleep(3600)
        msg = "📊 Сводка по сделкам за час:\n"
        for symbol, symbol_trades in trades.items():
            if symbol_trades:
                msg += f"\n[{symbol}]:\n"
                for t, p in symbol_trades:
                    msg += f"  {t}: BUY @ {p:.4f}\n"
                trades[symbol].clear()
        if msg.strip() != "📊 Сводка по сделкам за час:":
            send_telegram_message(msg)

def run_bot():
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 Бот запускается...")
    run_bot()
