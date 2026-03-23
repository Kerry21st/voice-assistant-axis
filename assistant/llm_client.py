"""
Клиент для общения с Ollama.
Поддерживает function calling.
"""

import requests
import json
from typing import List, Dict, Optional

class LlamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama3.1:8b", timeout=30):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.chat_url = f"{base_url}/api/chat"
    
    def send_message(self, message):
        """Отправляет одно сообщение."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        try:
            response = requests.post(self.chat_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            return f"Ошибка: {e}"
    
    def send_messages(self, messages):
        """Отправляет список сообщений."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        try:
            response = requests.post(self.chat_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            return f"Ошибка: {e}"
    
    def send_with_tools(self, messages, tools=None):
        """Отправляет сообщения с поддержкой инструментов."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        if tools:
            # В некоторых версиях Ollama параметр называется 'tools', в некоторых 'functions'
            payload["tools"] = tools
            
            # Для отладки выведем, что отправляем
            print(f"📤 Отправляю tools: {json.dumps(tools, indent=2, ensure_ascii=False)}")
        
        try:
            print(f"📤 Отправляю запрос к модели {self.model}")
            response = requests.post(self.chat_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP ошибка: {e}")
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"error": str(e)}
    
    def check_connection(self):
        """Проверяет доступность сервера."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# Для тестирования
if __name__ == "__main__":
    client = LlamaClient()
    if client.check_connection():
        print("✅ Подключение к Ollama работает")
        response = client.send_message("Привет, как дела?")
        print(f"Ответ: {response}")
    else:
        print("❌ Ollama не запущена")