
def run_bot():
    send_telegram_message("⚙️ run_bot() запускается")
    print("⚙️ run_bot() запускается")

    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=summary, daemon=True).start()

    while True:
        try:
            send_telegram_message("🔌 Подключение к WebSocket...")
            print("🔌 Подключение к WebSocket...")

            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/spot",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            send_telegram_message(f"❌ Ошибка подключения: {e}")
            print(f"❌ Ошибка подключения: {e}")
            time.sleep(10)
