"""
Главное окно чата с ассистентом.
Поддерживает текстовый ввод и голосовое распознавание (Vosk).
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTextEdit, QLineEdit, QPushButton)
from PySide6.QtCore import QThread, Signal, Qt

from assistant.core import Assistant
from assistant.tts_edge import TextToSpeech


class AssistantWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, assistant, message):
        super().__init__()
        self.assistant = assistant
        self.message = message

    def run(self):
        try:
            response = self.assistant.process_message(self.message)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class VoiceWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer

    def run(self):
        try:
            text = self.recognizer.listen_once()
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class TTSWorker(QThread):
    finished = Signal()

    def __init__(self, tts, text):
        super().__init__()
        self.tts = tts
        self.text = text

    def run(self):
        try:
            self.tts.speak(self.text)
        except Exception as e:
            print(f"Ошибка TTS: {e}")
        finally:
            self.finished.emit()


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AXIS — голосовой ассистент")
        self.setGeometry(100, 100, 700, 500)
        
        self.setMinimumSize(500, 400)

        self.load_styles()

        self.assistant = Assistant()

        self.recognizer = None
        self.load_speech_recognizer()

        self.tts = None
        self.load_tts()

        self.setup_ui()
        
        self.worker = None
        self.voice_worker = None

    def load_styles(self):
        try:
            with open("gui/style.qss", "r", encoding="utf-8") as f:
                style = f.read()
                self.setStyleSheet(style)
            print("✅ Стили загружены")
        except FileNotFoundError:
            print("⚠️ Файл стилей не найден, используются стандартные стили")

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.history = QTextEdit()
        self.history.setObjectName("historyEdit")
        self.history.setReadOnly(True)
        layout.addWidget(self.history)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Введите сообщение или нажмите 🎤...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("ОТПРАВИТЬ")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.clicked.connect(self.send_message)
        
        self.listen_btn = QPushButton("🎤")
        self.listen_btn.setObjectName("listenBtn")
        self.listen_btn.setFixedWidth(60)
        self.listen_btn.clicked.connect(self.start_listening)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.listen_btn)
        
        layout.addLayout(input_layout)

    def load_speech_recognizer(self):
        try:
            from assistant.stt import SpeechRecognizer
            self.recognizer = SpeechRecognizer()
            print("✅ Модель Vosk успешно загружена")
        except Exception as e:
            print(f"❌ Не удалось загрузить модель Vosk: {e}")
            self.recognizer = None

    def load_tts(self):
        try:
            self.tts = TextToSpeech(voice="ru-RU-SvetlanaNeural")
            print("✅ Модель TTS успешно загружена")
        except Exception as e:
            print(f"❌ Не удалось загрузить модель TTS: {e}")
            self.tts = None

    def add_message(self, sender, message, msg_type="user"):
        if msg_type == "user":
            html = f'<div class="message-user"><b>👤 ВЫ:</b> {message}</div>'
        elif msg_type == "assistant":
            html = f'<div class="message-assistant"><b>🤖 AXIS:</b> {message}</div>'
        elif msg_type == "system":
            html = f'<div class="message-system"><b>⚡ СИСТЕМА:</b> {message}</div>'
        elif msg_type == "error":
            html = f'<div class="message-error"><b>⚠️ ОШИБКА:</b> {message}</div>'
        elif msg_type == "listening":
            html = f'<div class="message-system listening-indicator"><b>🎤 СЛУШАЮ...</b> {message}</div>'
        else:
            html = f'<div>{message}</div>'
        
        self.history.append(html)
        self.history.verticalScrollBar().setValue(
            self.history.verticalScrollBar().maximum()
        )

    def send_message(self):
        msg = self.input_field.text().strip()
        if not msg:
            return

        self.add_message("user", msg, "user")
        self.input_field.clear()
        self.set_input_enabled(False)

        self.worker = AssistantWorker(self.assistant, msg)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.start()

    def set_input_enabled(self, enabled):
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.listen_btn.setEnabled(enabled)

    def on_response(self, response):
        self.add_message("assistant", response, "assistant")
        self.set_input_enabled(True)
        
        if self.tts is not None:
            self.tts_thread = TTSWorker(self.tts, response)
            self.tts_thread.finished.connect(self.tts_thread.deleteLater)
            self.tts_thread.start()

    def on_error(self, err_msg):
        self.add_message("system", err_msg, "error")
        self.set_input_enabled(True)

    def start_listening(self):
        if self.recognizer is None:
            self.add_message("system", "Модель Vosk не загружена", "error")
            return

        self.set_input_enabled(False)
        self.add_message("system", "Говорите...", "listening")
        
        self.voice_worker = VoiceWorker(self.recognizer)
        self.voice_worker.finished.connect(self.on_voice_result)
        self.voice_worker.error.connect(self.on_voice_error)
        self.voice_worker.finished.connect(self.voice_worker.deleteLater)
        self.voice_worker.error.connect(self.voice_worker.deleteLater)
        self.voice_worker.start()

    def on_voice_result(self, text):
        self.set_input_enabled(True)
        
        if text:
            self.add_message("user", f"🎤 {text}", "user")
            self.input_field.setText(text)
            self.send_message()
        else:
            self.add_message("system", "Ничего не распознано", "system")

    def on_voice_error(self, err_msg):
        self.set_input_enabled(True)
        self.add_message("system", f"Ошибка микрофона: {err_msg}", "error")