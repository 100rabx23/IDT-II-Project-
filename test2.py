import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.filedialog import askopenfilename
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import timedelta
from PIL import Image, ImageTk
import io


# Function to Filter Data Based on Timeframe
def filter_timeframe(data, timeframe):
    if timeframe == "1M":
        return data[-30:]
    elif timeframe == "6M":
        return data[-180:]
    elif timeframe == "1Y":
        return data[-365:]
    else:
        return data  # Full dataset


# Trend Detection Function using Moving Averages
def detect_trend(data):
    data['Short_MA'] = data['Close'].rolling(window=10).mean()
    data['Long_MA'] = data['Close'].rolling(window=50).mean()
    data['Trend'] = 'Neutral'
    data.loc[data['Short_MA'] > data['Long_MA'], 'Trend'] = 'Bullish'
    data.loc[data['Short_MA'] < data['Long_MA'], 'Trend'] = 'Bearish'
    return data


# Metrics Calculation
def calculate_metrics(data):
    data['Daily_Return'] = data['Close'].pct_change()
    avg_daily_return = data['Daily_Return'].mean()
    volatility = data['Daily_Return'].std()
    sharpe_ratio = avg_daily_return / volatility if volatility != 0 else 0
    high = data['Close'].max()
    low = data['Close'].min()
    returns = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
    return avg_daily_return, volatility, sharpe_ratio, high, low, returns


# Price Prediction Function
def predict_prices(data):
    model = LinearRegression()
    data['Day'] = np.arange(len(data))
    X = data[['Day']]
    y = data['Close']
    model.fit(X, y)

    # Predict for next 30 days
    future_days = np.arange(len(data), len(data) + 30).reshape(-1, 1)
    predictions = model.predict(future_days)

    prediction_dates = pd.date_range(start=data['Date'].iloc[-1] + timedelta(1), periods=30)
    return pd.DataFrame({'Date': prediction_dates, 'Predicted_Close': predictions})


# Plot Interactive Trend
def plot_interactive_trend(data, prediction=None):
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines+markers', name='Close Price',
                             line=dict(color='green', width=2)))
    if 'Short_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Short_MA'], mode='lines', name='10-Day MA', line=dict(color='orange')))
    if 'Long_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Long_MA'], mode='lines', name='50-Day MA', line=dict(color='blue')))
    if prediction is not None:
        fig.add_trace(go.Scatter(x=prediction['Date'], y=prediction['Predicted_Close'], mode='lines',
                                 name='Predicted Prices', line=dict(dash='dot', color='purple')))
    fig.update_layout(title='Stock Price Trend and Prediction', xaxis_title='Date', yaxis_title='Price',
                      hovermode='x unified', template='simple_white')
    return fig


# GUI Application
class StockApp(ttk.Window):
    def __init__(self, theme="darkly"):
        super().__init__(themename=theme)
        self.title("Stock Trend and Price Prediction")
        self.geometry("900x700")
        self.data = None

        # Top Frame: File Upload and Metrics
        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(fill=X, pady=10, padx=20)

        self.upload_button = ttk.Button(self.top_frame, text="Upload File", command=self.load_file, bootstyle=INFO)
        self.upload_button.pack(side=LEFT, padx=10)

        self.metrics_label = ttk.Label(self.top_frame, text="", font=("Helvetica", 10), bootstyle=LIGHT)
        self.metrics_label.pack(side=LEFT, padx=20)

        # Mid Frame: Timeframe Buttons
        self.mid_frame = ttk.Frame(self)
        self.mid_frame.pack(fill=X, pady=10, padx=20)

        for timeframe in ["1M", "6M", "1Y", "Max"]:
            ttk.Button(self.mid_frame, text=timeframe, command=lambda tf=timeframe: self.update_chart(tf),
                       bootstyle=OUTLINE).pack(side=LEFT, padx=5)

        # Predict Button
        self.predict_button = ttk.Button(self, text="Predict Future Prices", command=self.predict_future_prices,
                                          bootstyle=SUCCESS)
        self.predict_button.pack(pady=10)

        # Profitability Label
        self.profitability_label = ttk.Label(self, text="", font=("Helvetica", 12), bootstyle=SUCCESS)
        self.profitability_label.pack(pady=5)

        # Chart Display
        self.chart_canvas = ttk.Canvas(self, width=800, height=400)
        self.chart_canvas.pack(pady=10)

    def load_file(self):
        file_path = askopenfilename()
        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.data['Date'] = pd.to_datetime(self.data['Date'])
                self.data = detect_trend(self.data)
                self.update_chart("Max")
                avg_daily_return, volatility, sharpe_ratio, high, low, returns = calculate_metrics(self.data)
                self.metrics_label.config(
                    text=f"High: {high:.2f}, Low: {low:.2f}, Returns: {returns:.2f}%\n"
                         f"Sharpe Ratio: {sharpe_ratio:.4f}, Volatility: {volatility:.4f}")
            except Exception as e:
                self.metrics_label.config(text=f"Error: {e}")

    def update_chart(self, timeframe):
        if self.data is not None:
            filtered_data = filter_timeframe(self.data, timeframe)
            fig = plot_interactive_trend(filtered_data)
            self.display_chart(fig)

    def predict_future_prices(self):
        if self.data is not None:
            prediction_df = predict_prices(self.data)
            filtered_data = filter_timeframe(self.data, "Max")
            fig = plot_interactive_trend(filtered_data, prediction=prediction_df)
            self.display_chart(fig)

            is_profitable = prediction_df['Predicted_Close'].iloc[-1] > prediction_df['Predicted_Close'].iloc[0]
            self.profitability_label.config(
                text="Profitable to Buy" if is_profitable else "Not Profitable",
                bootstyle=SUCCESS if is_profitable else DANGER
            )

    def display_chart(self, fig):
        img_bytes = fig.to_image(format="png", width=800, height=400)
        img = Image.open(io.BytesIO(img_bytes))
        img_tk = ImageTk.PhotoImage(img)

        self.chart_canvas.delete("all")  # Clear previous chart
        self.chart_canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.chart_canvas.image = img_tk


# Run the Application
if __name__ == "__main__":
    app = StockApp(theme="darkly")
    app.mainloop()
