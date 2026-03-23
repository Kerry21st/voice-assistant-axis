"""
Модуль синтеза речи (TTS) на базе Silero.
Преобразует текст в голос и проигрывает его.
"""

import torch
import sounddevice as sd
import numpy as np
import time

class TextToSpeech:
    def __init__(self, speaker='baya_v2', sample_rate=16000, device=None):
        self.speaker = speaker
        self.sample_rate = sample_rate
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"🔄 Загрузка Silero TTS на {self.device}...")
        
        loaded = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker=self.speaker
        )
        
        self.model = loaded[0]
        self.model.to(self.device)
        print("✅ Silero TTS загружен")
    
    def speak(self, text):
        if not text or not isinstance(text, str):
            return
        
        # Ограничиваем длину текста (чтобы не обрывалось)
        if len(text) > 500:
            text = text[:500] + "..."
        
        print(f"🗣️ Озвучивание: {text[:50]}...")
        
        try:
            # Генерируем аудио
            audio = self.model.apply_tts(text, self.sample_rate)
            
            # Конвертируем в numpy
            if torch.is_tensor(audio):
                audio_numpy = audio.cpu().numpy()
            else:
                audio_numpy = np.array(audio)
            
            # Приводим к 1D массиву
            audio_numpy = audio_numpy.flatten()
            
            # Нормализуем для чистого звука (без искажений)
            audio_numpy = audio_numpy.astype(np.float32)
            
            # Мягкая нормализация (не обрезаем пики)
            max_val = np.max(np.abs(audio_numpy))
            if max_val > 1.0:
                audio_numpy = audio_numpy / max_val * 0.95  # оставляем запас 5%
            elif max_val < 0.1:
                audio_numpy = audio_numpy * 10  # усиливаем тихий звук
            
            print(f"📊 Аудио: длина={len(audio_numpy)}, "
                  f"min={audio_numpy.min():.3f}, max={audio_numpy.max():.3f}")
            
            # Проигрываем с явным указанием устройства
            sd.play(audio_numpy, samplerate=self.sample_rate)
            
            # Ждём окончания с запасом
            duration = len(audio_numpy) / self.sample_rate
            time.sleep(duration + 0.5)  # добавляем 0.5 секунды запаса
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    def speak_async(self, text):
        if not text:
            return None
        try:
            audio = self.model.apply_tts(text, self.sample_rate)
            return audio.cpu().numpy()
        except:
            return None