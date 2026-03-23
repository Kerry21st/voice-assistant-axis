"""
Модуль синтеза речи (TTS) на базе Edge-TTS.
Использует голоса Microsoft Edge.
"""

import asyncio
import edge_tts
import sounddevice as sd
import numpy as np
import io
import soundfile as sf

class TextToSpeech:
    """
    Класс для синтеза речи с использованием Edge-TTS.
    """
    
    def __init__(self, voice="ru-RU-DmitryNeural"):
        """
        Инициализация синтезатора речи.
        
        Аргументы:
            voice: имя голоса (ru-RU-DmitryNeural, ru-RU-SvetlanaNeural и др.)
        """
        self.voice = voice
        print(f"🔄 Загрузка Edge-TTS, голос: {voice}")
    
    def speak(self, text):
        """
        Произносит текст вслух.
        """
        if not text or not isinstance(text, str):
            return
        
        # Убедимся, что текст не пустой
        text = text.strip()
        if not text:
            return
        
        print(f"🗣️ Озвучивание: {text[:50]}...")
        
        # Запускаем асинхронную функцию
        try:
            asyncio.run(self._speak_async(text))
        except RuntimeError:
            # Если уже есть запущенный цикл событий
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._speak_async(text))
            loop.close()
    
    async def _speak_async(self, text):
        """Асинхронная генерация и воспроизведение речи."""
        try:
            # Создаём поток для генерации аудио
            communicate = edge_tts.Communicate(text, self.voice)
            
            # Собираем аудио в буфер
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if not audio_data:
                print("❌ Не получены аудиоданные")
                return
            
            # Конвертируем в numpy массив через soundfile
            audio_bytes = io.BytesIO(audio_data)
            audio, samplerate = sf.read(audio_bytes)
            
            # Приводим к float32
            audio = audio.astype(np.float32)
            
            # Если стерео, конвертируем в моно
            if len(audio.shape) == 2:
                audio = audio.mean(axis=1)
            
            print(f"📊 Аудио: длина={len(audio)} сэмплов, частота={samplerate}Гц")
            
            # Проигрываем
            sd.play(audio, samplerate)
            sd.wait()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


# Тестирование при прямом запуске
if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование Edge-TTS")
    print("=" * 60)
    
    # Список голосов для тестирования (по отдельности)
    voices_to_try = [
        "en-GB-RyanNeural",     # британский,
        "en-GB-ThomasNeural",    # ещё британский
        "en-US-GuyNeural",       # американский диктор
        "ru-RU-DmitryNeural",    # русский мужской
        "ru-RU-SvetlanaNeural"   # русский женский
    ]
    
    for voice in voices_to_try:
        print(f"\n🎤 Пробуем голос: {voice}")
        tts = TextToSpeech(voice=voice)
        # Для английских голосов — английский текст
        if voice.startswith("en"):
            tts.speak("Hello sir, I am your personal assistant. All systems are operational.")
        # Для русских — русский текст
        else:
            tts.speak("Открой файл project_config.json в папке Downloads")
        
        # Спрашиваем, хочет ли пользователь продолжить
        answer = input("Продолжить тест? (y/n): ")
        if answer.lower() != 'y':
            break