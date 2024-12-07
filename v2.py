import time
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import requests

# Setup for logging (file and terminal)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_robot.log'),
        logging.StreamHandler()  # Log to terminal as well
    ]
)

# Telegram configuration for notifications
TELEGRAM_TOKEN = 'your_telegram_bot_token'
TELEGRAM_CHAT_ID = 'your_chat_id'

def send_telegram_message(message):
    """Sends a message to a configured Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Error sending Telegram notification: {e}")

# Binance API keys
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'

# Initialize Binance client
client = Client(API_KEY, API_SECRET)

# Configuration parameters
CAPITAL = 100  # Total capital in USDT
PROFIT_TARGET = 0.05  # Profit target: 5%
COST_AVERAGING_STEP = 0.015  # Cost averaging step: 1.5%
SLEEP_TIME = 300  # Time between cycles in seconds (5 minutes)

# Helper function to calculate Volume Moving Average (VMA)
def calculate_vma(volumes, window=5):
    """Calculates the Volume Moving Average (VMA)."""
    return sum(volumes[-window:]) / window

# Helper function to calculate Rate of Change (ROC)
def calculate_roc(data):
    """Calculates the percentage change (Rate of Change) over the data."""
    return ((data[-1] - data[0]) / data[0]) * 100

# Helper function to calculate Exponential Moving Average (EMA)
def calculate_ema(data, window):
    """Calculates the Exponential Moving Average (EMA)."""
    alpha = 2 / (window + 1)
    ema = [data[0]]
    for price in data[1:]:
        ema.append((price * alpha) + (ema[-1] * (1 - alpha)))
    return ema

# Fetch top gainers with 1-hour change between 4% and 6%
def fetch_top_gainers():
    """Fetches top gainers from Binance within the 4-6% range."""
    try:
        tickers = client.get_ticker()
        gainers = [
            t for t in tickers 
            if float(t['priceChangePercent']) >= 4 and float(t['priceChangePercent']) <= 6 
            and t['symbol'].endswith('USDT')
        ]
        logging.info(f"Top gainers retrieved: {[g['symbol'] for g in gainers]}")
        return gainers
    except BinanceAPIException as e:
        logging.error(f"Binance API error while fetching tickers: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching tickers: {e}")
        return []

# Analyze momentum using 15-minute Klines, ROC, and VMA
def analyze_momentum(symbol):
    """Analyzes momentum of a symbol based on price and volume trends."""
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=15)
        close_prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        # Calculate metrics for momentum analysis
        price_roc = calculate_roc(close_prices)
        current_volume = volumes[-1]
        vma = calculate_vma(volumes)
        rvol = current_volume / vma

        # Check for consistent price increase and high relative volume
        if price_roc > 2 and rvol > 1.5:  # Example thresholds
            logging.info(f"Bullish momentum detected for {symbol}: Price ROC={price_roc:.2f}%, RVOL={rvol:.2f}")
            return True

        logging.info(f"No strong momentum for {symbol}: Price ROC={price_roc:.2f}%, RVOL={rvol:.2f}")
        return False
    except BinanceAPIException as e:
        logging.error(f"Binance API error while analyzing momentum for {symbol}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while analyzing momentum for {symbol}: {e}")
        return False

# Execute a trade for a given symbol
def execute_trade(symbol, amount):
    """Executes a market buy order for a given symbol."""
    try:
        order = client.order_market_buy(symbol=symbol, quantity=amount)
        logging.info(f"Order executed for {symbol}: {order}")
        send_telegram_message(f"Trade executed for {symbol}: {order}")
        return order
    except BinanceOrderException as e:
        logging.error(f"Order execution error for {symbol}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during order execution for {symbol}: {e}")

# Main trading loop
def main():
    logging.info("Starting the trading bot...")
    send_telegram_message("Trading bot successfully started!")

    while True:
        try:
            # Step 1: Identify promising coins
            gainers = fetch_top_gainers()
            for gainer in gainers:
                symbol = gainer['symbol']
                if analyze_momentum(symbol):
                    # Step 2: Strategically invest in coins with strong momentum
                    execute_trade(symbol, CAPITAL * 0.25)  # Example: 25% of capital
                    time.sleep(10)  # Avoid trading too frequently

            # Wait before the next cycle
            logging.info("Cycle complete, waiting for the next...")
            time.sleep(SLEEP_TIME)
        except Exception as e:
            logging.error(f"Unexpected error in the main loop: {e}")
            send_telegram_message(f"Error in trading bot: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    main()
