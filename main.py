import tkinter as tk
from src.gui import TranslaterApp

def main():
    root = tk.Tk()
    app = TranslaterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
