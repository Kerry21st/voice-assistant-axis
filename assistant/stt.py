"""
Модуль распознавания речи (STT) на базе Vosk.
Преобразует голос с микрофона в текст.
"""

import json
import queue
import os
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer


class SpeechRecognizer:
    """
    Класс для распознавания речи с микрофона.
    
    Использование:
        recognizer = SpeechRecognizer()
        text = recognizer.listen_once()
        print(f"Вы сказали: {text}")
    """
    
    def __init__(self, model_path="models/vosk-model-small-ru-0.22", samplerate=16000):
        """
        Инициализация распознавателя.
        
        Аргументы:
            model_path: путь к папке с моделью Vosk (относительно корня проекта)
            samplerate: частота дискретизации (16000 Гц требуется для Vosk)
        """
        # Проверяем, существует ли папка с моделью
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Модель не найдена по пути: {model_path}\n"
                "Убедись, что модель скачана и распакована в правильную папку."
            )
        
        # Загружаем модель Vosk (это может занять несколько секунд)
        print(f"Загрузка модели из {model_path}...")
        self.model = Model(model_path)
        self.samplerate = samplerate
        
        # Создаём распознаватель
        self.recognizer = KaldiRecognizer(self.model, samplerate)
        
        # Очередь для передачи аудиоданных из callback'а в основной поток
        self.audio_queue = queue.Queue()
        
        print("Модель загружена, можно начинать распознавание.")
    
    def callback(self, indata, frames, time_info, status):
        """
        Callback-функция для sounddevice.
        Вызывается автоматически для каждого блока аудио с микрофона.
        
        Аргументы:
            indata: массив с аудиоданными
            frames: количество фреймов
            time_info: информация о времени (не используется)
            status: статус записи (ошибки и т.п.)
        """
        if status:
            print(f"⚠️ Статус аудио: {status}")
        
        # Кладём аудиоданные в очередь для обработки в основном потоке
        self.audio_queue.put(bytes(indata))
    
    def listen(self, timeout=5):
        """
        Слушает микрофон и возвращает распознанный текст.
        
        Аргументы:
            timeout: максимальное время ожидания речи в секундах
        
        Возвращает:
            str: распознанный текст или пустую строку, если ничего не распознано
        """
        print("🎤 Слушаю... (говорите)")
        
        # Открываем поток с микрофона
        with sd.RawInputStream(
            samplerate=self.samplerate,      # частота дискретизации
            blocksize=8000,                   # размер блока (рекомендовано для Vosk)
            device=None,                       # None = устройство по умолчанию
            dtype='int16',                     # формат данных (требуется Vosk)
            channels=1,                         # моно (Vosk работает с моно)
            callback=self.callback              # функция, вызываемая для каждого блока
        ):
            start_time = time.time()
            
            while True:
                # Проверяем, не истекло ли время ожидания
                if time.time() - start_time > timeout:
                    print("⏱️ Таймаут (ничего не сказано)")
                    return ""
                
                # Берём следующий блок аудио из очереди
                data = self.audio_queue.get()
                
                # Передаём данные в распознаватель Vosk
                if self.recognizer.AcceptWaveform(data):
                    # Распознан законченный фрагмент (обычно после паузы)
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '')
                    
                    if text:
                        print(f"✅ Распознано: {text}")
                        return text
                else:
                    # Получаем промежуточный результат (то, что распознано пока не полностью)
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '')
                    
                    if partial_text:
                        # Выводим промежуточный результат на той же строке (динамическое обновление)
                        print(f"🔄 Промежуточно: {partial_text}", end='\r')
    
    def listen_once(self):
        """
        Упрощённый метод для однократного прослушивания.
        Использует таймаут по умолчанию (5 секунд).
        
        Возвращает:
            str: распознанный текст
        """
        return self.listen(timeout=5)


# Блок для тестирования при прямом запуске файла
if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование распознавания речи (Vosk)")
    print("Скажите что-нибудь в микрофон")
    print("=" * 60)
    
    try:
        # Создаём распознаватель
        recognizer = SpeechRecognizer()
        
        # Слушаем и распознаём
        text = recognizer.listen_once()
        
        # Выводим результат
        if text:
            print(f"\n✅ Вы сказали: {text}")
        else:
            print("\n❌ Ничего не распознано")
            
    except FileNotFoundError as e:
        print(f"\n❌ Ошибка: {e}")
        print("   Убедись, что модель скачана и распакована в папку 'models/'")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")