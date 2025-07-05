import time
import threading
from collections import deque
from config import SYMBOLS
from telegram_utils import send_telegram_message

volatility_data = {symbol: deque(maxlen=30) for symbol in SYMBOLS}

def update_volatility(symbol, mid_price):
    volatility_data[symbol].append(mid_price)

def analyze_volatility():
    while True:
        time.sleep(300)  # каждые 5 минут
        message = "📈 Волатильность рынка:\n"
        for symbol, prices in volatility_data.items():
            if len(prices) < 2:
                message += f"{symbol}: недостаточно данных\n"
                continue
            change = abs(prices[-1] - prices[0]) / prices[0]
            status = "волатилен" if change >= 0.005 else "низкая волатильность"
            message += f"{symbol}: {status} (Δ={change*100:.2f}%)\n"
        send_telegram_message(message)

def start_volatility_analysis():
    thread = threading.Thread(target=analyze_volatility, daemon=True)
    thread.start()
