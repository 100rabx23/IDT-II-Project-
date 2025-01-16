import os
import io
import numpy as np
import pandas as pd
from datetime import timedelta
from tkinter import Tk, Canvas, Label, Button, Frame, filedialog
from sklearn.linear_model import LinearRegression
from PIL import Image, ImageTk
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Data Filtering
def filter_timeframe(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1M":
        return data[-30:]
    elif timeframe == "6M":
        return data[-180:]
    elif timeframe == "1Y":
        return data[-365:]
    return data

# Trend Detection
def detect_trend(data: pd.DataFrame) -> pd.DataFrame:
    data['Short_MA'] = data['Close'].rolling(window=10).mean()
    data['Long_MA'] = data['Close'].rolling(window=50).mean()
    data['Trend'] = np.where(data['Short_MA'] > data['Long_MA'], 'Bullish', 'Bearish')
    return data

# Metrics Calculation
def calculate_metrics(data: pd.DataFrame) -> tuple:
    try:
        data['Close'] = pd.to_numeric(data['Close'], errors='coerce').dropna()
        data['Daily_Return'] = data['Close'].pct_change()
        avg_daily_return = data['Daily_Return'].mean()
        volatility = data['Daily_Return'].std()
        sharpe_ratio = avg_daily_return / volatility if volatility != 0 else 0
        high, low = data['Close'].max(), data['Close'].min()
        returns = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        return avg_daily_return, volatility, sharpe_ratio, high, low, returns
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return 0, 0, 0, 0, 0, 0

# Price Prediction
def predict_prices(data: pd.DataFrame) -> pd.DataFrame:
    model = LinearRegression()
    data['Day'] = np.arange(len(data))
    model.fit(data[['Day']], data['Close'])
    future_days = np.arange(len(data), len(data) + 30).reshape(-1, 1)
    predictions = model.predict(future_days)
    prediction_dates = pd.date_range(data['Date'].iloc[-1] + timedelta(days=1), periods=30)
    return pd.DataFrame({'Date': prediction_dates, 'Predicted_Close': predictions})

# Interactive Plot
def plot_interactive_trend(data: pd.DataFrame, prediction: pd.DataFrame = None) -> go.Figure:
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='Close Price', line=dict(color='green')))
    if 'Short_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Short_MA'], name='10-Day MA', line=dict(color='orange')))
    if 'Long_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Long_MA'], name='50-Day MA', line=dict(color='blue')))
    if prediction is not None:
        fig.add_trace(go.Scatter(x=prediction['Date'], y=prediction['Predicted_Close'], name='Predicted Prices', line=dict(dash='dot', color='purple')))
    fig.update_layout(title='Stock Price Trend', template='plotly_white', xaxis_title='Date', yaxis_title='Price')
    return fig

# PDF Generation
def generate_pdf(data: pd.DataFrame, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Stock Trend Analysis Report", styles['Title']))
    elements.append(Spacer(1, 12))
    table_data = [["Stock Name", "High", "Low", "Returns (%)", "Sharpe Ratio"]]
    table_data.append([
        data.get('Stock Name', 'N/A'),
        f"{data['Close'].max():.2f}",
        f"{data['Close'].min():.2f}",
        f"{calculate_metrics(data)[5]:.2f}",
        f"{calculate_metrics(data)[2]:.2f}",
    ])
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    elements.append(table)
    doc.build(elements)

# GUI Setup
def load_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        try:
            root.data = pd.read_csv(file_path, parse_dates=['Date'])
            root.data = detect_trend(root.data)
            update_chart("Max")
            avg_return, vol, sharpe, high, low, ret = calculate_metrics(root.data)
            metrics_label.config(text=f"High: {high:.2f}, Low: {low:.2f}, Returns: {ret:.2f}%")
        except Exception as e:
            metrics_label.config(text=f"Error loading data: {e}")

def update_chart(timeframe: str):
    if hasattr(root, 'data'):
        filtered_data = filter_timeframe(root.data, timeframe)
        fig = plot_interactive_trend(filtered_data)
        display_chart(fig)

def display_chart(fig: go.Figure):
    img_bytes = fig.to_image(format="png")
    img = Image.open(io.BytesIO(img_bytes))
    img_tk = ImageTk.PhotoImage(img)
    chart_canvas.create_image(0, 0, anchor="nw", image=img_tk)
    chart_canvas.image = img_tk

# Main GUI Application
root = Tk()
root.title("Stock Trend Analysis")
root.geometry("800x600")

upload_button = Button(root, text="Upload CSV", command=load_file, bg="lightblue")
upload_button.pack(pady=10)

metrics_label = Label(root, text="", font=("Helvetica", 12))
metrics_label.pack(pady=5)

frame_buttons = Frame(root)
frame_buttons.pack()
for tf in ["1M", "6M", "1Y", "Max"]:
    Button(frame_buttons, text=tf, command=lambda t=tf: update_chart(t), width=8).pack(side="left", padx=5)

chart_canvas = Canvas(root, width=800, height=400, bg="white")
chart_canvas.pack(pady=10)

root.mainloop()
