"""
main.py
-------
Starts the Flood Risk Analysis & Prediction System.
Run with:  python main.py
"""

import tkinter as tk

from gui import FloodApp


def main():
    root = tk.Tk()
    FloodApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
