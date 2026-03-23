"""
Долговременная память с использованием LLM для извлечения фактов.
"""

import json
import os
from datetime import datetime

class MemoryLLM:
    def __init__(self, memory_file="logs/memory.json"):
        self.memory_file = memory_file
        self.data = self._load()
    
    def _load(self):
        """Загружает память из файла."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"facts": {}, "conversations": []}
        return {"facts": {}, "conversations": []}
    
    def _save(self):
        """Сохраняет память в файл."""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def remember_fact(self, category, key, value):
        """Сохраняет факт, поддерживая множественные значения."""
        if not key or not value:
            return
        
        if category not in self.data["facts"]:
            self.data["facts"][category] = {}
        
        # Если факт с таким ключом уже существует
        if key in self.data["facts"][category]:
            existing = self.data["facts"][category][key]["value"]
            
            # Если это список, добавляем новое значение
            if isinstance(existing, list):
                if value not in existing:
                    existing.append(value)
                    self.data["facts"][category][key]["value"] = existing
            else:
                # Превращаем в список
                if existing != value:
                    self.data["facts"][category][key]["value"] = [existing, value]
        else:
            # Новый факт
            self.data["facts"][category][key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
        
        self._save()
        print(f"📝 Запомнил: {category}.{key} = {self.data['facts'][category][key]['value']}")
    
    def recall_fact(self, category, key):
        """Возвращает конкретный факт."""
        if category in self.data["facts"] and key in self.data["facts"][category]:
            return self.data["facts"][category][key]["value"]
        return None
    
    def recall_all_facts(self):
        """Возвращает все факты в виде текста для системного промпта."""
        if not self.data["facts"]:
            return ""
        
        result = "📌 Информация о пользователе:\n"
        for category, items in self.data["facts"].items():
            for key, fact in items.items():
                result += f"- {key}: {fact['value']}\n"
        return result
    
    def get_all_facts_json(self):
        """Возвращает все факты в виде JSON."""
        facts_dict = {}
        for category, items in self.data["facts"].items():
            for key, fact in items.items():
                facts_dict[f"{category}.{key}"] = fact["value"]
        return facts_dict