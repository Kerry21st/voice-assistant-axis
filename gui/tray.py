import sys
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMainWindow)
from PySide6.QtGui import QIcon, QAction
from gui.main_window import ChatWindow

class TrayApp(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)  # или self.show_window(), если хочешь сразу показать
        self.setIcon("gui/resources/Tabler-icons_icons.png")
        print("Иконка трея создана, проверь трей")
        self.setToolTip("Голосовой ассистент")

        # Создаём главное окно (но не показываем сразу)
        self.window = ChatWindow()

        self.window.show()

        # Меню трея
        menu = QMenu()
        show_action = QAction("Показать окно", self)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        listen_action = QAction("Слушать (голос)", self)
        listen_action.triggered.connect(self.start_listening)
        menu.addAction(listen_action)

        menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)

        self.setContextMenu(menu)
        self.show()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def start_listening(self):
        # Пока заглушка, позже добавим голос
        print("Голосовое распознавание ещё не реализовано")

    def exit_app(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Проверяем, есть ли иконка; если нет, используем стандартную
    tray = TrayApp()
    sys.exit(app.exec())