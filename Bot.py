import time
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import requests

# Configuration des logs
logging.basicConfig(
    filename='trading_robot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration de Telegram
TELEGRAM_TOKEN = 'votre_telegram_bot_token'
TELEGRAM_CHAT_ID = 'votre_chat_id'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de notification Telegram : {e}")

# Clés API Binance
API_KEY = 'votre_api_key'
API_SECRET = 'votre_api_secret'

# Initialisation du client Binance
client = Client(API_KEY, API_SECRET)

# Configuration des paramètres du robot
CAPITAL = 100  # Capital total en USDT
PROFIT_TARGET = 0.05  # Objectif de profit : 5%
COST_AVERAGING_STEP = 0.015  # Baisse de prix pour moyenne du coût : 1.5%
SLEEP_TIME = 300  # Temps d'attente entre les cycles en secondes (5 minutes)

def fetch_top_gainers():
    """Récupère les pièces avec les meilleurs gains sur 1 heure."""
    try:
        tickers = client.get_ticker()
        gainers = [
            t for t in tickers 
            if float(t['priceChangePercent']) >= 4 and float(t['priceChangePercent']) <= 6 
            and t['symbol'].endswith('USDT')
        ]
        logging.info(f"Top gagnants récupérés : {[g['symbol'] for g in gainers]}")
        return gainers
    except BinanceAPIException as e:
        logging.error(f"Erreur API Binance lors de la récupération des tickers : {e}")
        return []
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la récupération des tickers : {e}")
        return []

def analyze_momentum(symbol):
    """Analyse le momentum d'une pièce sur les 15 dernières minutes."""
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=15)
        close_prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        if all(x < y for x, y in zip(close_prices, close_prices[1:])) and all(x < y for x, y in zip(volumes, volumes[1:])):
            logging.info(f"Momentum haussier détecté pour {symbol}")
            return True
        return False
    except BinanceAPIException as e:
        logging.error(f"Erreur API Binance lors de l'analyse du momentum pour {symbol} : {e}")
        return False
    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'analyse du momentum pour {symbol} : {e}")
        return False

def execute_trade(symbol, amount):
    """Exécute un trade pour une pièce donnée."""
    try:
        order = client.order_market_buy(symbol=symbol, quantity=amount)
        logging.info(f"Ordre exécuté pour {symbol} : {order}")
        send_telegram_message(f"Trade exécuté pour {symbol} : {order}")
        return order
    except BinanceOrderException as e:
        logging.error(f"Erreur lors de l'exécution de l'ordre pour {symbol} : {e}")
    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'exécution de l'ordre pour {symbol} : {e}")

def main():
    logging.info("Démarrage du robot de trading...")
    send_telegram_message("Robot de trading démarré avec succès !")

    while True:
        try:
            # Étape 1 : Identifier les pièces prometteuses
            gainers = fetch_top_gainers()
            for gainer in gainers:
                symbol = gainer['symbol']
                if analyze_momentum(symbol):
                    # Étape 2 : Investir stratégiquement
                    execute_trade(symbol, CAPITAL * 0.25)  # Exemple : 25% du capital
                    # Pause pour éviter trop de trades simultanés
                    time.sleep(10)
            # Attendre avant le prochain cycle
            logging.info("Cycle terminé, attente avant le prochain...")
            time.sleep(SLEEP_TIME)
        except Exception as e:
            logging.error(f"Erreur inattendue dans la boucle principale : {e}")
            send_telegram_message(f"Erreur dans le robot : {e}")
            time.sleep(60)  # Attendre 1 minute avant de réessayer

if __name__ == "__main__":
    main()
