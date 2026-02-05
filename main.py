import customtkinter as ctk
from src.gui import TranslaterApp

def main():
    root = ctk.CTk()
    app = TranslaterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
