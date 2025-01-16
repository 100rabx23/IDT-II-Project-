import tkinter as tk
from tkinter import ttk

class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Dashboard")
        self.geometry("800x600")
        self.configure(bg="#1e1e2f")  # Dark background for a professional look

        # Define available timeframes and default color
        self.timeframes = ["1D", "1W", "1M", "1Y"]
        self.default_color = "#444"  # Default button color

        # Frame for buttons
        self.button_frame = tk.Frame(self, bg="#1e1e2f")
        self.button_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Create buttons for each timeframe
        for timeframe in self.timeframes:
            button = self.create_button(
                timeframe, 
                callback=lambda tf=timeframe: self.update_chart(tf), 
                color=self.default_color
            )
            button.pack(side=tk.LEFT, padx=5)

        # Placeholder for the chart area
        self.chart_label = tk.Label(
            self, text="Chart Area", bg="#1e1e2f", fg="white", font=("Arial", 14)
        )
        self.chart_label.pack(expand=True)

    def create_button(self, label, callback, color):
        """Create a button with hover effects."""
        button = tk.Label(
            self.button_frame,
            text=label,
            bg=color,
            fg="white",
            font=("Arial", 12),
            padx=10,
            pady=5,
            relief=tk.RAISED,
            cursor="hand2",
        )
        button.bind("<Button-1>", lambda e: callback())
        button.bind("<Enter>", lambda e: button.config(bg=self.lighten_color(color)))
        button.bind("<Leave>", lambda e: button.config(bg=color))
        return button

    def darken_color(self, color, factor=0.8):
        """Darken a hex color."""
        try:
            r, g, b = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"
        except ValueError:
            return "#333"  # Fallback to a default dark color

    def lighten_color(self, color, factor=1.2):
        """Lighten a hex color."""
        try:
            r, g, b = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except ValueError:
            return "#555"  # Fallback to a default light color

    def update_chart(self, timeframe):
        """Update the chart area based on the selected timeframe."""
        self.chart_label.config(text=f"Chart for {timeframe}")

# Run the application
if __name__ == "__main__":
    window = StockApp()
    window.mainloop()
