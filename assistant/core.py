"""
Ядро ассистента с долговременной памятью.
Использует LLM для извлечения фактов из диалогов.
"""

import json
import re
from datetime import datetime
from .llm_client import LlamaClient
from .memory_llm import MemoryLLM


class Assistant:
    def __init__(self, model_name="llama3.1:8b"):
        self.llm = LlamaClient(model=model_name)
        self.history = []
        self.memory = MemoryLLM()
        print("✅ Ассистент AXIS загружен с LLM-памятью")

    def is_simple_query(self, text):
        """Определяет, простой ли запрос (можно ответить быстрой моделью)."""
        simple_keywords = [
            'открой', 'запусти', 'включи', 'открыть', 'запустить',
            'время', 'дата', 'сколько время', 'который час',
            'калькулятор', 'браузер', 'проводник', 'блокнот',
            'привет', 'пока', 'спасибо', 'здравствуй',
            'как дела', 'что делаешь', 'кто ты',
            'яндекс', 'гугл', 'ютуб', 'кинопоиск',
            'сайт', 'мой сайт', 'fieldmate'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in simple_keywords)

    def should_extract_facts(self, user_text, assistant_response):
        """
        Определяет, стоит ли анализировать диалог на предмет фактов.
        """
        # Проверяем, есть ли в диалоге что-то похожее на факт
        indicators = [
            "зовут", "меня зовут", "меня", "мне", "я", "люблю", 
            "нравится", "работаю", "учусь", "живу", "моя", "мой", 
            "моё", "называют", "предпочитаю", "обожаю"
        ]
        
        text = user_text.lower()
        response = assistant_response.lower() if assistant_response else ""
        
        # Проверяем пользовательское сообщение
        if any(ind in text for ind in indicators):
            return True
        
        # Проверяем, не спрашивает ли ассистент (чтобы не анализировать вопросы)
        if "?" in assistant_response or "как" in response or "что" in response:
            return False
        
        # Если в ответе есть "запомнил" или "понял" — значит факт был извлечён
        if "запомни" in response or "понял" in response:
            return True
        
        return False

    def extract_facts_with_llm(self, user_text, assistant_response):
        """
        Использует LLM для извлечения фактов из диалога.
        """
        prompt = f"""Проанализируй этот диалог и извлеки факты о пользователе.

    Диалог:
    Пользователь: {user_text}
    Ассистент: {assistant_response}

    Правила:
    1. Используй ТОЛЬКО эти категории:
    - личное (имя, возраст, город, день_рождения)
    - работа (профессия, компания, навыки, проекты)
    - привычки (любит, не_любит, хобби, распорядок)
    - предпочтения (музыка, фильмы, еда, напитки, машины)
    - расписание (встречи, дела, напоминания)

    2. Разделяй разные вещи в разные факты:
    - "люблю пельмени и борщ" → два отдельных факта: "пельмени" и "борщ"
    - "люблю кофе и чай" → два факта

    3. Используй понятные ключи без опечаток:
    - для еды: "еда" (не "кушать")
    - для любимых вещей: "любит"

    4. Примеры правильного извлечения:
    Пользователь: "меня зовут Дима, я люблю пельмени и борщ"
    Ответ: {{"факты": [
        {{"категория": "личное", "ключ": "имя", "значение": "Дима"}},
        {{"категория": "привычки", "ключ": "любит", "значение": "пельмени"}},
        {{"категория": "привычки", "ключ": "любит", "значение": "борщ"}}
    ]}}

    5. Если в одной категории несколько значений, создавай отдельные факты.
    6. Если нет новых фактов, верни пустой список: {{"факты": []}}

    Верни только JSON, без пояснений."""

        try:
            response = self.llm.send_message(prompt)
            
            # Извлекаем JSON из ответа
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                facts = data.get("факты", [])
                
                for fact in facts:
                    category = fact.get("категория", "личное")
                    key = fact.get("ключ")
                    value = fact.get("значение")
                    
                    # Исправляем типичные опечатки
                    key_corrections = {
                        "любиет": "любит",
                        "любиет_кушать": "еда",
                        "кушать": "еда",
                        "люблю": "любит"
                    }
                    key = key_corrections.get(key, key)
                    
                    # Нормализуем категорию
                    category = category.lower()
                    category_corrections = {
                        "пребаения": "предпочтения",
                        "привычкии": "привычки",
                        "личност": "личное"
                    }
                    category = category_corrections.get(category, category)
                    
                    self.memory.remember_fact(category, key, value)
                return len(facts)
        except Exception as e:
            print(f"⚠️ Ошибка извлечения фактов: {e}")
        
        return 0

    def process_message(self, user_text):
        from .system_commands import TOOLS, FUNCTIONS

        # Получаем все факты из памяти для контекста
        facts = self.memory.recall_all_facts()
        
        # Строим системный промпт с фактами
        system_prompt_content = f"""Ты — голосовой ассистент AXIS. Отвечай кратко, уверенно, в технологичном стиле.

{facts if facts else "Информация о пользователе пока не сохранена."}

ВАЖНО: 
- Используй информацию из фактов, когда это уместно.
- Если знаешь имя пользователя, обращайся по имени.
- Если знаешь предпочтения, учитывай их.

Различай похожие функции:
- open_calculator — только для калькулятора (математика)
- open_timer — для таймеров и напоминаний по времени

Алгоритм работы:
1. Выслушай запрос пользователя
2. Если нужно выполнить действие — вызови соответствующую функцию
3. После получения результата функции, сообщи пользователю, что ты сделал
4. Не просто возвращай результат функции, а комментируй его

Примеры:
Пользователь: "какое сейчас время"
Ты вызываешь get_time() → получаешь "Сейчас 14:30"
Ты отвечаешь: "Сейчас 14:30."

Пользователь: "открой калькулятор"
Ты вызываешь open_calculator() → получаешь "✅ Калькулятор открыт"
Ты отвечаешь: "Калькулятор открыт. Можете пользоваться."

Пользователь: "меня зовут Дима"
Ты отвечаешь: "Запомнил, Дима. Приятно познакомиться!"

Пользователь: "привет"
Ты отвечаешь: "AXIS на связи. Чем могу помочь?" """

        # Добавляем системный промпт, если его нет
        if not self.history or self.history[0].get("role") != "system":
            self.history.insert(0, {"role": "system", "content": system_prompt_content})
        else:
            # Обновляем существующий системный промпт (на случай новых фактов)
            self.history[0]["content"] = system_prompt_content

        # Добавляем сообщение пользователя
        self.history.append({"role": "user", "content": user_text})

        # Выбираем модель в зависимости от сложности запроса
        if self.is_simple_query(user_text):
            self.llm.model = "llama3.2:3b"
            print("⚡ Использую быструю модель для простого запроса")
        else:
            self.llm.model = "llama3.1:8b"
            print("🧠 Использую умную модель для сложного запроса")
        
        # Первый запрос к модели (может вызвать функции)
        response = self.llm.send_with_tools(self.history, tools=TOOLS)
        
        if "error" in response:
            return f"Ошибка: {response['error']}"

        message = response['message']
        
        # Добавляем ответ модели в историю
        self.history.append({"role": "assistant", "content": message.get('content', '')})

        # Обрабатываем вызовы функций, если они есть
        if 'tool_calls' in message and message['tool_calls']:
            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                func_args = tool_call['function']['arguments']

                # Парсим аргументы
                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except:
                        func_args = {}

                # Вызываем функцию
                if func_name in FUNCTIONS:
                    try:
                        result = FUNCTIONS[func_name](**func_args)
                    except Exception as e:
                        result = f"❌ Ошибка: {e}"
                else:
                    result = f"❌ Функция {func_name} не найдена"

                # Добавляем результат функции в историю
                self.history.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.get('id', '')
                })

            # Второй запрос к модели для финального ответа
            final_response = self.llm.send_with_tools(self.history)
            
            if "error" in final_response:
                return f"Ошибка: {final_response['error']}"
            
            if 'message' in final_response and 'content' in final_response['message']:
                final_message = final_response['message']['content']
                self.history.append({"role": "assistant", "content": final_message})
                
                # Извлекаем факты из диалога (если нужно)
                if self.should_extract_facts(user_text, final_message):
                    extracted = self.extract_facts_with_llm(user_text, final_message)
                    if extracted > 0:
                        print(f"📝 Извлечено {extracted} новых фактов")
                
                return final_message
            else:
                return "Я выполнил команду, но не могу сформулировать ответ."
        else:
            # Обычный текстовый ответ без вызова функций
            content = message.get('content', '')
            
            # Извлекаем факты из диалога (если нужно)
            if self.should_extract_facts(user_text, content):
                extracted = self.extract_facts_with_llm(user_text, content)
                if extracted > 0:
                    print(f"📝 Извлечено {extracted} новых фактов")
            
            return content

    def clear_history(self):
        """Очищает историю текущего диалога."""
        self.history = []
        print("🧹 История диалога очищена")