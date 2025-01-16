from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
import io
from PIL import Image

class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Trend and Price Prediction")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #1e1e2f; color: white; font-family: 'Arial';")
        self.data = None

        # Main Container
        container = QWidget()
        layout = QVBoxLayout(container)

        # Upload Button
        self.upload_button = self.create_button(
            "Upload File", icon="folder-open", callback=self.load_file, color="#0078d7"
        )
        layout.addWidget(self.upload_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Metrics Display
        self.metrics_label = QLabel("Upload a file to see metrics.")
        self.metrics_label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(self.metrics_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Timeframe Buttons
        self.timeframe_layout = QHBoxLayout()
        for timeframe in ["1M", "6M", "1Y", "Max"]:
            button = self.create_button(timeframe, callback=lambda tf=timeframe: self.update_chart(tf))
            self.timeframe_layout.addWidget(button)
        layout.addLayout(self.timeframe_layout)

        # Predict Button
        self.predict_button = self.create_button(
            "Predict Future Prices", icon="line-chart", callback=self.predict_future_prices, color="#28a745"
        )
        layout.addWidget(self.predict_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Profitability Label
        self.profitability_label = QLabel("")
        self.profitability_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.profitability_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Chart Display
        self.chart_label = QLabel()
        self.chart_label.setStyleSheet("border: 1px solid #444; background-color: #252530;")
        layout.addWidget(self.chart_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(container)

    def create_button(self, text, icon=None, callback=None, color="#444"):
        """Create a styled button with optional icon and callback."""
        button = QPushButton(text)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.lighten_color(color)};
            }}
            """
        )
        if icon:
            button.setIcon(QIcon(f"icons/{icon}.png"))  # Use appropriate icon file paths.
        if callback:
            button.clicked.connect(callback)
        return button

    def darken_color(self, color, factor=0.8):
        """Darken a hex color."""
        r, g, b = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"

    def lighten_color(self, color, factor=1.2):
        """Lighten a hex color."""
        r, g, b = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        r, g, b = [min(int(c * factor), 255) for c in (r, g, b)]
        return f"#{r:02x}{g:02x}{b:02x}"

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.data['Date'] = pd.to_datetime(self.data['Date'])
                avg_daily_return, volatility, sharpe_ratio, high, low, returns = self.calculate_metrics(self.data)
                self.metrics_label.setText(
                    f"High: {high:.2f}, Low: {low:.2f}, Returns: {returns:.2f}%\n"
                    f"Sharpe Ratio: {sharpe_ratio:.4f}, Volatility: {volatility:.4f}"
                )
                self.update_chart("Max")
            except Exception as e:
                self.metrics_label.setText(f"Error: {e}")

    def update_chart(self, timeframe):
        if self.data is not None:
            filtered_data = self.filter_timeframe(self.data, timeframe)
            fig = self.plot_interactive_trend(filtered_data)
            self.display_chart(fig)

    def predict_future_prices(self):
        if self.data is not None:
            prediction_df = self.predict_prices(self.data)
            filtered_data = self.filter_timeframe(self.data, "Max")
            fig = self.plot_interactive_trend(filtered_data, prediction_df)
            self.display_chart(fig)

            is_profitable = prediction_df['Predicted_Close'].iloc[-1] > prediction_df['Predicted_Close'].iloc[0]
            self.profitability_label.setText(
                "Profitable to Buy" if is_profitable else "Not Profitable"
            )
            self.profitability_label.setStyleSheet(
                "color: #28a745;" if is_profitable else "color: #dc3545;"
            )

    def display_chart(self, fig):
        img_bytes = fig.to_image(format="png", width=800, height=400)
        img = Image.open(io.BytesIO(img_bytes))
        img.save("chart.png")  # Save the image locally
        pixmap = QPixmap("chart.png")
        self.chart_label.setPixmap(pixmap)

    # Supporting Functions (Metrics, Prediction, etc.)
    # ... (same as before)


# Run the Application
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = StockApp()
    window.show()
    sys.exit(app.exec())
