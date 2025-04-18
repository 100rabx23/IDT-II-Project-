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
    },
    'AXISBANK.NS': {
        'currentPrice': 950.75,
        'marketCap': 2.8e12,
        'trailingPE': 19.8,
        'fiftyTwoWeekHigh': 1050.25,
        'fiftyTwoWeekLow': 850.50
    },
    'BAJAJFINSV.NS': {
        'currentPrice': 1500.50,
        'marketCap': 2.2e12,
        'trailingPE': 35.5,
        'fiftyTwoWeekHigh': 1650.75,
        'fiftyTwoWeekLow': 1350.25
    },
    'BAJFINANCE.NS': {
        'currentPrice': 6500.25,
        'marketCap': 3.8e12,
        'trailingPE': 28.7,
        'fiftyTwoWeekHigh': 7000.50,
        'fiftyTwoWeekLow': 6000.25
    },
    'HCLTECH.NS': {
        'currentPrice': 1200.75,
        'marketCap': 3.2e12,
        'trailingPE': 22.3,
        'fiftyTwoWeekHigh': 1300.50,
        'fiftyTwoWeekLow': 1100.25
    },
    'ITC.NS': {
        'currentPrice': 400.50,
        'marketCap': 5.0e12,
        'trailingPE': 25.5,
        'fiftyTwoWeekHigh': 450.75,
        'fiftyTwoWeekLow': 350.25
    },
    'LT.NS': {
        'currentPrice': 3200.25,
        'marketCap': 4.5e12,
        'trailingPE': 30.2,
        'fiftyTwoWeekHigh': 3500.50,
        'fiftyTwoWeekLow': 2900.25
    },
    'MARUTI.NS': {
        'currentPrice': 9000.75,
        'marketCap': 2.7e12,
        'trailingPE': 32.5,
        'fiftyTwoWeekHigh': 9500.50,
        'fiftyTwoWeekLow': 8500.25
    },
    'NESTLEIND.NS': {
        'currentPrice': 22000.50,
        'marketCap': 2.1e12,
        'trailingPE': 75.3,
        'fiftyTwoWeekHigh': 23000.75,
        'fiftyTwoWeekLow': 21000.25
    },
    'ONGC.NS': {
        'currentPrice': 200.25,
        'marketCap': 2.5e12,
        'trailingPE': 5.8,
        'fiftyTwoWeekHigh': 220.50,
        'fiftyTwoWeekLow': 180.25
    },
    'POWERGRID.NS': {
        'currentPrice': 250.75,
        'marketCap': 2.3e12,
        'trailingPE': 15.2,
        'fiftyTwoWeekHigh': 280.50,
        'fiftyTwoWeekLow': 220.25
    },
    'SUNPHARMA.NS': {
        'currentPrice': 1200.50,
        'marketCap': 2.8e12,
        'trailingPE': 35.7,
        'fiftyTwoWeekHigh': 1300.75,
        'fiftyTwoWeekLow': 1100.25
    },
    'TECHM.NS': {
        'currentPrice': 1100.25,
        'marketCap': 1.8e12,
        'trailingPE': 20.3,
        'fiftyTwoWeekHigh': 1200.50,
        'fiftyTwoWeekLow': 1000.25
    },
    'ULTRACEMCO.NS': {
        'currentPrice': 8000.75,
        'marketCap': 2.3e12,
        'trailingPE': 28.5,
        'fiftyTwoWeekHigh': 8500.50,
        'fiftyTwoWeekLow': 7500.25
    },
    'ASIANPAINT.NS': {
        'currentPrice': 3000.50,
        'marketCap': 2.9e12,
        'trailingPE': 65.2,
        'fiftyTwoWeekHigh': 3200.75,
        'fiftyTwoWeekLow': 2800.25
    },
    'BAJAJ-AUTO.NS': {
        'currentPrice': 4000.25,
        'marketCap': 1.2e12,
        'trailingPE': 18.7,
        'fiftyTwoWeekHigh': 4200.50,
        'fiftyTwoWeekLow': 3800.25
    },
    'BRITANNIA.NS': {
        'currentPrice': 4500.75,
        'marketCap': 1.1e12,
        'trailingPE': 45.3,
        'fiftyTwoWeekHigh': 4700.50,
        'fiftyTwoWeekLow': 4300.25
    },
    'CIPLA.NS': {
        'currentPrice': 1200.50,
        'marketCap': 1.5e12,
        'trailingPE': 25.8,
        'fiftyTwoWeekHigh': 1300.75,
        'fiftyTwoWeekLow': 1100.25
    },
    'DRREDDY.NS': {
        'currentPrice': 5500.25,
        'marketCap': 1.8e12,
        'trailingPE': 30.2,
        'fiftyTwoWeekHigh': 5800.50,
        'fiftyTwoWeekLow': 5200.25
    },
    'EICHERMOT.NS': {
        'currentPrice': 3500.75,
        'marketCap': 1.0e12,
        'trailingPE': 35.5,
        'fiftyTwoWeekHigh': 3700.50,
        'fiftyTwoWeekLow': 3300.25
    },
    'GRASIM.NS': {
        'currentPrice': 1800.50,
        'marketCap': 1.2e12,
        'trailingPE': 20.3,
        'fiftyTwoWeekHigh': 1900.75,
        'fiftyTwoWeekLow': 1700.25
    },
    'HDFCLIFE.NS': {
        'currentPrice': 600.25,
        'marketCap': 1.3e12,
        'trailingPE': 65.7,
        'fiftyTwoWeekHigh': 650.50,
        'fiftyTwoWeekLow': 550.25
    },
    'HEROMOTOCO.NS': {
        'currentPrice': 3000.75,
        'marketCap': 0.9e12,
        'trailingPE': 22.5,
        'fiftyTwoWeekHigh': 3200.50,
        'fiftyTwoWeekLow': 2800.25
    },
    'INDUSINDBK.NS': {
        'currentPrice': 1400.50,
        'marketCap': 1.1e12,
        'trailingPE': 15.8,
        'fiftyTwoWeekHigh': 1500.75,
        'fiftyTwoWeekLow': 1300.25
    },
    'JSWSTEEL.NS': {
        'currentPrice': 800.25,
        'marketCap': 1.9e12,
        'trailingPE': 12.3,
        'fiftyTwoWeekHigh': 850.50,
        'fiftyTwoWeekLow': 750.25
    },
    'M&M.NS': {
        'currentPrice': 1500.75,
        'marketCap': 1.8e12,
        'trailingPE': 18.5,
        'fiftyTwoWeekHigh': 1600.50,
        'fiftyTwoWeekLow': 1400.25
    },
    'NTPC.NS': {
        'currentPrice': 200.50,
        'marketCap': 2.0e12,
        'trailingPE': 10.2,
        'fiftyTwoWeekHigh': 220.75,
        'fiftyTwoWeekLow': 180.25
    },
    'SBILIFE.NS': {
        'currentPrice': 1200.25,
        'marketCap': 1.2e12,
        'trailingPE': 55.7,
        'fiftyTwoWeekHigh': 1300.50,
        'fiftyTwoWeekLow': 1100.25
    },
    'SHREECEM.NS': {
        'currentPrice': 25000.75,
        'marketCap': 0.9e12,
        'trailingPE': 30.5,
        'fiftyTwoWeekHigh': 26000.50,
        'fiftyTwoWeekLow': 24000.25
    },
    'TATACONSUM.NS': {
        'currentPrice': 800.50,
        'marketCap': 0.8e12,
        'trailingPE': 45.2,
        'fiftyTwoWeekHigh': 850.75,
        'fiftyTwoWeekLow': 750.25
    },
    'TATASTEEL.NS': {
        'currentPrice': 120.25,
        'marketCap': 1.5e12,
        'trailingPE': 8.3,
        'fiftyTwoWeekHigh': 130.50,
        'fiftyTwoWeekLow': 110.25
    },
    'UPL.NS': {
        'currentPrice': 600.75,
        'marketCap': 0.7e12,
        'trailingPE': 15.5,
        'fiftyTwoWeekHigh': 650.50,
        'fiftyTwoWeekLow': 550.25
    },
    'ADANIPORTS.NS': {
        'currentPrice': 800.50,
        'marketCap': 1.7e12,
        'trailingPE': 22.3,
        'fiftyTwoWeekHigh': 850.75,
        'fiftyTwoWeekLow': 750.25
    },
    'APOLLOHOSP.NS': {
        'currentPrice': 5000.25,
        'marketCap': 0.7e12,
        'trailingPE': 85.7,
        'fiftyTwoWeekHigh': 5200.50,
        'fiftyTwoWeekLow': 4800.25
    },
    'BAJAJHLDNG.NS': {
        'currentPrice': 7000.75,
        'marketCap': 1.1e12,
        'trailingPE': 25.5,
        'fiftyTwoWeekHigh': 7300.50,
        'fiftyTwoWeekLow': 6700.25
    },
    'BPCL.NS': {
        'currentPrice': 400.50,
        'marketCap': 0.9e12,
        'trailingPE': 8.2,
        'fiftyTwoWeekHigh': 420.75,
        'fiftyTwoWeekLow': 380.25
    },
    'COALINDIA.NS': {
        'currentPrice': 300.25,
        'marketCap': 1.8e12,
        'trailingPE': 7.3,
        'fiftyTwoWeekHigh': 320.50,
        'fiftyTwoWeekLow': 280.25
    },
    'DIVISLAB.NS': {
        'currentPrice': 3500.75,
        'marketCap': 0.8e12,
        'trailingPE': 45.5,
        'fiftyTwoWeekHigh': 3700.50,
        'fiftyTwoWeekLow': 3300.25
    },
    'HINDALCO.NS': {
        'currentPrice': 500.50,
        'marketCap': 1.1e12,
        'trailingPE': 12.2,
        'fiftyTwoWeekHigh': 520.75,
        'fiftyTwoWeekLow': 480.25
    },
    'IOC.NS': {
        'currentPrice': 150.25,
        'marketCap': 1.3e12,
        'trailingPE': 6.3,
        'fiftyTwoWeekHigh': 160.50,
        'fiftyTwoWeekLow': 140.25
    },
    'SBIN.NS': {
        'currentPrice': 600.75,
        'marketCap': 5.4e12,
        'trailingPE': 15.5,
        'fiftyTwoWeekHigh': 650.50,
        'fiftyTwoWeekLow': 550.25
    },
    'TATAPOWER.NS': {
        'currentPrice': 300.50,
        'marketCap': 0.9e12,
        'trailingPE': 18.2,
        'fiftyTwoWeekHigh': 320.75,
        'fiftyTwoWeekLow': 280.25
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
            'WIPRO': {'symbol': 'WIPRO.NS', 'name': 'Wipro'},
            'AXIS': {'symbol': 'AXISBANK.NS', 'name': 'Axis Bank'},
            'BAJAJFINSV': {'symbol': 'BAJAJFINSV.NS', 'name': 'Bajaj Finserv'},
            'BAJFINANCE': {'symbol': 'BAJFINANCE.NS', 'name': 'Bajaj Finance'},
            'HCL': {'symbol': 'HCLTECH.NS', 'name': 'HCL Technologies'},
            'ITC': {'symbol': 'ITC.NS', 'name': 'ITC Limited'},
            'LT': {'symbol': 'LT.NS', 'name': 'Larsen & Toubro'},
            'MARUTI': {'symbol': 'MARUTI.NS', 'name': 'Maruti Suzuki'},
            'NESTLE': {'symbol': 'NESTLEIND.NS', 'name': 'Nestle India'},
            'ONGC': {'symbol': 'ONGC.NS', 'name': 'Oil & Natural Gas Corporation'},
            'POWERGRID': {'symbol': 'POWERGRID.NS', 'name': 'Power Grid Corporation'},
            'SUNPHARMA': {'symbol': 'SUNPHARMA.NS', 'name': 'Sun Pharmaceutical'},
            'TECHM': {'symbol': 'TECHM.NS', 'name': 'Tech Mahindra'},
            'ULTRACEMCO': {'symbol': 'ULTRACEMCO.NS', 'name': 'UltraTech Cement'},
            'ASIANPAINT': {'symbol': 'ASIANPAINT.NS', 'name': 'Asian Paints'},
            'BAJAJ-AUTO': {'symbol': 'BAJAJ-AUTO.NS', 'name': 'Bajaj Auto'},
            'BRITANNIA': {'symbol': 'BRITANNIA.NS', 'name': 'Britannia Industries'},
            'CIPLA': {'symbol': 'CIPLA.NS', 'name': 'Cipla'},
            'DRREDDY': {'symbol': 'DRREDDY.NS', 'name': 'Dr. Reddy\'s Laboratories'},
            'EICHERMOT': {'symbol': 'EICHERMOT.NS', 'name': 'Eicher Motors'},
            'GRASIM': {'symbol': 'GRASIM.NS', 'name': 'Grasim Industries'},
            'HDFCLIFE': {'symbol': 'HDFCLIFE.NS', 'name': 'HDFC Life Insurance'},
            'HEROMOTOCO': {'symbol': 'HEROMOTOCO.NS', 'name': 'Hero MotoCorp'},
            'INDUSINDBK': {'symbol': 'INDUSINDBK.NS', 'name': 'IndusInd Bank'},
            'JSWSTEEL': {'symbol': 'JSWSTEEL.NS', 'name': 'JSW Steel'},
            'M&M': {'symbol': 'M&M.NS', 'name': 'Mahindra & Mahindra'},
            'NTPC': {'symbol': 'NTPC.NS', 'name': 'NTPC Limited'},
            'SBILIFE': {'symbol': 'SBILIFE.NS', 'name': 'SBI Life Insurance'},
            'SHREECEM': {'symbol': 'SHREECEM.NS', 'name': 'Shree Cement'},
            'TATACONSUM': {'symbol': 'TATACONSUM.NS', 'name': 'Tata Consumer Products'},
            'TATASTEEL': {'symbol': 'TATASTEEL.NS', 'name': 'Tata Steel'},
            'UPL': {'symbol': 'UPL.NS', 'name': 'UPL Limited'},
            'ADANIPORTS': {'symbol': 'ADANIPORTS.NS', 'name': 'Adani Ports'},
            'APOLLOHOSP': {'symbol': 'APOLLOHOSP.NS', 'name': 'Apollo Hospitals'},
            'BAJAJHLDNG': {'symbol': 'BAJAJHLDNG.NS', 'name': 'Bajaj Holdings'},
            'BPCL': {'symbol': 'BPCL.NS', 'name': 'Bharat Petroleum'},
            'COALINDIA': {'symbol': 'COALINDIA.NS', 'name': 'Coal India'},
            'DIVISLAB': {'symbol': 'DIVISLAB.NS', 'name': 'Divis Laboratories'},
            'HINDALCO': {'symbol': 'HINDALCO.NS', 'name': 'Hindalco Industries'},
            'IOC': {'symbol': 'IOC.NS', 'name': 'Indian Oil Corporation'},
            'SBIN': {'symbol': 'SBIN.NS', 'name': 'State Bank of India'},
            'TATAPOWER': {'symbol': 'TATAPOWER.NS', 'name': 'Tata Power'}
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