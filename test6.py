import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from tkinter import Canvas, Tk, filedialog, Button, Label, Frame
import tkinter as tk
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image, ImageTk
import io
import os

# Data Processing Functions
def filter_timeframe(data, timeframe):
    """Filter data based on the selected timeframe."""
    days_map = {"1M": 30, "6M": 180, "1Y": 365}
    return data[-days_map.get(timeframe, len(data)):]

def detect_trend(data):
    """Add trend detection using moving averages."""
    data['Short_MA'] = data['Close'].rolling(window=10).mean()
    data['Long_MA'] = data['Close'].rolling(window=50).mean()
    data['Trend'] = np.where(data['Short_MA'] > data['Long_MA'], 'Bullish', 'Bearish')
    return data

def calculate_metrics(data):
    """Calculate stock performance metrics."""
    data['Daily_Return'] = data['Close'].pct_change()
    avg_daily_return = data['Daily_Return'].mean()
    volatility = data['Daily_Return'].std()
    sharpe_ratio = avg_daily_return / volatility if volatility else 0
    high, low = data['Close'].max(), data['Close'].min()
    total_returns = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
    return avg_daily_return, volatility, sharpe_ratio, high, low, total_returns

def predict_prices(data):
    """Predict future stock prices using Linear Regression."""
    model = LinearRegression()
    data['Day'] = np.arange(len(data))
    X, y = data[['Day']], data['Close']
    model.fit(X, y)

    future_days = np.arange(len(data), len(data) + 30).reshape(-1, 1)
    predictions = model.predict(future_days)
    prediction_dates = pd.date_range(start=data['Date'].iloc[-1] + timedelta(1), periods=30)
    return pd.DataFrame({'Date': prediction_dates, 'Predicted_Close': predictions})

# Visualization Functions
def plot_interactive_trend(data, prediction=None):
    """Create an interactive stock trend plot."""
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='Close Price'))
    if 'Short_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Short_MA'], mode='lines', name='10-Day MA'))
    if 'Long_MA' in data.columns:
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Long_MA'], mode='lines', name='50-Day MA'))
    if prediction is not None:
        fig.add_trace(go.Scatter(x=prediction['Date'], y=prediction['Predicted_Close'], mode='lines', name='Prediction'))
    fig.update_layout(title="Stock Trend", xaxis_title="Date", yaxis_title="Price", template="plotly_dark")
    return fig

# PDF Report Generation
def generate_pdf(data, output_path="Stock_Report.pdf"):
    """Generate a PDF report of stock data."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Stock Trend Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    headers = ["Date", "Close", "Short_MA", "Long_MA", "Trend"]
    table_data = [headers] + data[headers].fillna("").values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(table)
    doc.build(elements)

# GUI Functions
def load_file():
    """Load stock data from a CSV file."""
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            root.data = pd.read_csv(file_path, parse_dates=['Date'])
            if not {'Date', 'Close'}.issubset(root.data.columns):
                raise ValueError("CSV must contain 'Date' and 'Close' columns.")
            root.data = detect_trend(root.data)
            update_chart("1Y")
            display_metrics()
        except Exception as e:
            metrics_label.config(text=f"Error: {e}")

def update_chart(timeframe):
    """Update the stock chart for the selected timeframe."""
    if hasattr(root, 'data'):
        filtered_data = filter_timeframe(root.data, timeframe)
        fig = plot_interactive_trend(filtered_data)
        display_chart(fig)

def predict_future():
    """Predict future stock prices and update the chart."""
    if hasattr(root, 'data'):
        prediction = predict_prices(root.data)
        filtered_data = filter_timeframe(root.data, "1Y")
        fig = plot_interactive_trend(filtered_data, prediction)
        display_chart(fig)

def display_metrics():
    """Calculate and display stock performance metrics."""
    if hasattr(root, 'data'):
        avg_daily_return, volatility, sharpe_ratio, high, low, total_returns = calculate_metrics(root.data)
        metrics_label.config(
            text=(f"High: {high:.2f}, Low: {low:.2f}, Returns: {total_returns:.2f}%\n"
                  f"Sharpe Ratio: {sharpe_ratio:.4f}, Volatility: {volatility:.4f}, Avg Return: {avg_daily_return:.4f}")
        )

def display_chart(fig):
    """Render the chart on the GUI."""
    img_bytes = fig.to_image(format="png", width=800, height=400)
    img = Image.open(io.BytesIO(img_bytes))
    img_tk = ImageTk.PhotoImage(img)
    chart_canvas.delete("all")
    chart_canvas.create_image(0, 0, anchor="nw", image=img_tk)
    chart_canvas.image = img_tk

# GUI Setup
root = Tk()
root.title("Stock Analysis Tool")
root.geometry("900x700")
root.configure(bg="#2E3440")  # Dark theme background

# Styles
def style_button(btn, hover_color="#3B4252", active_color="#4C566A"):
    """Apply hover and active effects to buttons."""
    def on_enter(e):
        btn['bg'] = hover_color
    def on_leave(e):
        btn['bg'] = "#434C5E"
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.configure(bg="#434C5E", fg="#ECEFF4", relief="flat", activebackground=active_color, font=("Helvetica", 12))

Button(root, text="Upload File", command=load_file).pack(pady=10)
style_button(Button(root, text="Upload File", command=load_file))

metrics_label = Label(root, text="", bg="#2E3440", fg="#ECEFF4", font=("Helvetica", 12))
metrics_label.pack(pady=10)

frame_buttons = Frame(root, bg="#2E3440")
frame_buttons.pack(pady=10)

for tf in ["1M", "6M", "1Y", "Max"]:
    btn = Button(frame_buttons, text=tf, command=lambda t=tf: update_chart(t), width=10)
    btn.pack(side="left", padx=5)
    style_button(btn)

predict_btn = Button(root, text="Predict Future", command=predict_future)
predict_btn.pack(pady=10)
style_button(predict_btn, hover_color="#A3BE8C", active_color="#8FBCBB")

pdf_btn = Button(root, text="Generate PDF Report", command=lambda: generate_pdf(root.data))
pdf_btn.pack(pady=10)
style_button(pdf_btn, hover_color="#BF616A", active_color="#D08770")

chart_canvas = Canvas(root, width=800, height=400, bg="#3B4252", highlightthickness=0)
chart_canvas.pack(pady=20)

root.mainloop()
