from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import time
from functools import lru_cache
import random
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Sample historical data for fallback
SAMPLE_DATA = {
    'TATAMOTORS.NS': {
        'currentPrice': 800.50,
        'marketCap': 2.5e12,
        'trailingPE': 15.2,
        'fiftyTwoWeekHigh': 900.75,
        'fiftyTwoWeekLow': 650.25
    },
    'RELIANCE.NS': {
        'currentPrice': 2500.75,
        'marketCap': 15.8e12,
        'trailingPE': 22.5,
        'fiftyTwoWeekHigh': 2800.50,
        'fiftyTwoWeekLow': 2200.25
    },
    'INFY.NS': {
        'currentPrice': 1500.25,
        'marketCap': 6.2e12,
        'trailingPE': 28.3,
        'fiftyTwoWeekHigh': 1700.50,
        'fiftyTwoWeekLow': 1300.75
    },
    'HDFCBANK.NS': {
        'currentPrice': 1600.50,
        'marketCap': 8.5e12,
        'trailingPE': 18.7,
        'fiftyTwoWeekHigh': 1800.25,
        'fiftyTwoWeekLow': 1400.50
    },
    'TCS.NS': {
        'currentPrice': 3500.75,
        'marketCap': 12.5e12,
        'trailingPE': 30.2,
        'fiftyTwoWeekHigh': 3800.50,
        'fiftyTwoWeekLow': 3200.25
    },
    'ICICIBANK.NS': {
        'currentPrice': 900.25,
        'marketCap': 6.8e12,
        'trailingPE': 20.5,
        'fiftyTwoWeekHigh': 1000.50,
        'fiftyTwoWeekLow': 800.25
    },
    'BHARTIARTL.NS': {
        'currentPrice': 850.50,
        'marketCap': 4.8e12,
        'trailingPE': 25.3,
        'fiftyTwoWeekHigh': 900.75,
        'fiftyTwoWeekLow': 700.25
    },
    'HINDUNILVR.NS': {
        'currentPrice': 2500.25,
        'marketCap': 5.8e12,
        'trailingPE': 60.2,
        'fiftyTwoWeekHigh': 2800.50,
        'fiftyTwoWeekLow': 2200.25
    },
    'KOTAKBANK.NS': {
        'currentPrice': 1800.50,
        'marketCap': 3.5e12,
        'trailingPE': 25.7,
        'fiftyTwoWeekHigh': 2000.75,
        'fiftyTwoWeekLow': 1600.25
    },
    'WIPRO.NS': {
        'currentPrice': 450.25,
        'marketCap': 2.5e12,
        'trailingPE': 18.3,
        'fiftyTwoWeekHigh': 500.50,
        'fiftyTwoWeekLow': 400.25
    }
}

# Sample news data
SAMPLE_NEWS = {
    'TATAMOTORS.NS': [
        {'title': 'Tata Motors reports strong Q3 results', 'date': '2024-02-15', 'source': 'Economic Times'},
        {'title': 'Tata Motors launches new electric vehicle', 'date': '2024-02-10', 'source': 'Business Standard'},
        {'title': 'Tata Motors expands production capacity', 'date': '2024-02-05', 'source': 'Moneycontrol'}
    ],
    'RELIANCE.NS': [
        {'title': 'Reliance Industries announces new investments', 'date': '2024-02-14', 'source': 'Economic Times'},
        {'title': 'Reliance Jio reports record subscriber growth', 'date': '2024-02-08', 'source': 'Business Standard'},
        {'title': 'Reliance Retail expands operations', 'date': '2024-02-03', 'source': 'Moneycontrol'}
    ],
    'INFY.NS': [
        {'title': 'Infosys signs major deal with global client', 'date': '2024-02-13', 'source': 'Economic Times'},
        {'title': 'Infosys announces new AI initiatives', 'date': '2024-02-07', 'source': 'Business Standard'},
        {'title': 'Infosys reports strong Q3 performance', 'date': '2024-02-02', 'source': 'Moneycontrol'}
    ]
}

def generate_sample_history(base_price, days=365):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
    prices = [base_price * (1 + random.uniform(-0.02, 0.02)) for _ in range(days)]
    volumes = [random.randint(1000000, 5000000) for _ in range(days)]
    return pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'Volume': volumes
    })

@lru_cache(maxsize=32)
def get_cached_stock(symbol):
    try:
        # Try to get real data first
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info:
            raise Exception("No data available")
        return stock
    except Exception as e:
        print(f"Using sample data for {symbol} due to: {str(e)}")
        # Create a mock stock object with sample data
        class MockStock:
            def __init__(self, symbol):
                self.symbol = symbol
                self.info = SAMPLE_DATA.get(symbol, SAMPLE_DATA['TATAMOTORS.NS'])
            
            def history(self, period):
                return generate_sample_history(self.info['currentPrice'])
        
        return MockStock(symbol)

def get_indian_stock(symbol):
    if '.' not in symbol:
        symbol += '.NS'
    return get_cached_stock(symbol)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')
        stocks = {
            'TATA': {'symbol': 'TATAMOTORS.NS', 'name': 'Tata Motors'},
            'RELIANCE': {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries'},
            'INFY': {'symbol': 'INFY.NS', 'name': 'Infosys'},
            'HDFC': {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank'},
            'TCS': {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services'},
            'ICICI': {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank'},
            'BHARTI': {'symbol': 'BHARTIARTL.NS', 'name': 'Bharti Airtel'},
            'HUL': {'symbol': 'HINDUNILVR.NS', 'name': 'Hindustan Unilever'},
            'KOTAK': {'symbol': 'KOTAKBANK.NS', 'name': 'Kotak Mahindra Bank'},
            'WIPRO': {'symbol': 'WIPRO.NS', 'name': 'Wipro'}
        }
        results = [v for k,v in stocks.items() if query.upper() in k]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stock/<symbol>')
def get_stock(symbol):
    try:
        stock = get_indian_stock(symbol)
        hist = stock.history(period="1y")
        
        if hist.empty:
            hist = generate_sample_history(stock.info['currentPrice'])
        
        hist = hist.reset_index()
        hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        
        # Prediction model
        df = hist.copy()
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['Signal'] = np.where(df['Close'].shift(-5) > df['Close'], 1, 0)
        df = df.dropna()
        
        X = df[['SMA_20', 'SMA_50', 'Volume']]
        y = df['Signal']
        
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X, y)
        
        latest = df.iloc[-1]
        prediction = model.predict([[latest['SMA_20'], latest['SMA_50'], latest['Volume']]])[0]
        recommendation = 'BUY' if prediction == 1 else 'SELL'
        
        return jsonify({
            'symbol': symbol,
            'price': round(stock.info['currentPrice'], 2),
            'hist': hist[['Date','Close','Volume']].to_dict(orient='records'),
            'recommendation': recommendation,
            'info': {
                'marketCap': stock.info['marketCap'],
                'peRatio': stock.info['trailingPE'],
                'weekHigh': stock.info['fiftyTwoWeekHigh'],
                'weekLow': stock.info['fiftyTwoWeekLow']
            }
        })
    except Exception as e:
        print(f"Error processing stock data: {str(e)}")
        return jsonify({'error': 'Error processing stock data'}), 500

@app.route('/news/<symbol>')
def get_news(symbol):
    try:
        # In a real application, you would fetch news from a news API
        # For now, we'll return sample news data
        news = SAMPLE_NEWS.get(symbol, [])
        if not news:
            # Generate sample news for stocks without predefined news
            company_name = symbol.split('.')[0]
            news = [
                {
                    'title': f'{company_name} reports strong quarterly results',
                    'date': (datetime.now() - timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d'),
                    'source': 'Economic Times'
                },
                {
                    'title': f'{company_name} announces new business initiatives',
                    'date': (datetime.now() - timedelta(days=random.randint(16, 30))).strftime('%Y-%m-%d'),
                    'source': 'Business Standard'
                },
                {
                    'title': f'{company_name} expands market presence',
                    'date': (datetime.now() - timedelta(days=random.randint(31, 45))).strftime('%Y-%m-%d'),
                    'source': 'Moneycontrol'
                }
            ]
        return jsonify(news)
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return jsonify({'error': 'Error fetching news'}), 500

if __name__ == '__main__':
    app.run(debug=True)