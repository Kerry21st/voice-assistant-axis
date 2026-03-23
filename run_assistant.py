#!/usr/bin/env python
import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import ChatWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AXIS Assistant")
    app.setApplicationDisplayName("AXIS — голосовой ассистент")
    
    window = ChatWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()