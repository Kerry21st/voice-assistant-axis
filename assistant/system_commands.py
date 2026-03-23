"""
Модуль для выполнения системных команд.
Открытие программ, работа с файлами и т.д.
"""

import subprocess
import os
import webbrowser
import shutil
from datetime import datetime
import threading
import time
import json

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================

def find_program_path(program_name):
    """Ищет программу в системе по имени."""
    # Список возможных путей для популярных программ
    common_paths = [
        os.path.expandvars(r"%ProgramFiles%"),
        os.path.expandvars(r"%ProgramFiles(x86)%"),
        os.path.expandvars(r"%LocalAppData%\Programs"),
        os.path.expandvars(r"%AppData%\..\Local\Programs"),
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        os.path.expandvars(r"%UserProfile%\AppData\Local"),
        os.path.expandvars(r"%UserProfile%\AppData\Roaming"),
        os.path.expandvars(r"%UserProfile%\Desktop"),
        os.path.expandvars(r"%UserProfile%\Downloads")
    ]
    
    # Словарь соответствия названий и исполняемых файлов
    program_executables = {
        "яндекс музыка": ["yandex music.exe", "yandex-music.exe", "YandexMusic.exe", "music.exe"],
        "yandex music": ["yandex music.exe", "yandex-music.exe", "YandexMusic.exe", "music.exe"],
        "яндекс": ["yandex.exe", "Yandex.exe", "browser.exe", "yandexbrowser.exe"],
        "yandex": ["yandex.exe", "Yandex.exe", "browser.exe", "yandexbrowser.exe"],
        "google chrome": ["chrome.exe", "Google Chrome.exe"],
        "chrome": ["chrome.exe", "Google Chrome.exe"],
        "firefox": ["firefox.exe", "Firefox.exe"],
        "telegram": ["Telegram.exe", "Telegram Desktop.exe"],
        "telegram desktop": ["Telegram.exe", "Telegram Desktop.exe"],
        "discord": ["Discord.exe", "Discord.exe"],
        "whatsapp": ["WhatsApp.exe", "WhatsAppDesktop.exe"],
        "zoom": ["Zoom.exe", "Zoom.exe"],
        "skype": ["Skype.exe", "Skype.exe"],
        "steam": ["Steam.exe", "Steam.exe"],
        "epic games": ["EpicGamesLauncher.exe"],
        "visual studio code": ["Code.exe", "VSCode.exe"],
        "vscode": ["Code.exe", "VSCode.exe"],
        "редактор кода": ["Code.exe", "VSCode.exe"],
        "pycharm": ["pycharm64.exe", "pycharm.exe"],
        "word": ["WINWORD.EXE", "Word.exe"],
        "excel": ["EXCEL.EXE", "Excel.exe"],
        "powerpoint": ["POWERPNT.EXE", "PowerPoint.exe"],
        "outlook": ["OUTLOOK.EXE", "Outlook.exe"],
        "калькулятор": ["calc.exe"],
        "блокнот": ["notepad.exe"],
        "проводник": ["explorer.exe"],
        "командная строка": ["cmd.exe"],
        "cmd": ["cmd.exe"],
        "диспетчер задач": ["taskmgr.exe"],
        "регулировка громкости": ["sndvol.exe"],
        "экранная клавиатура": ["osk.exe"],
        "paint": ["mspaint.exe"],
        "паинт": ["mspaint.exe"],
        "spotify": ["Spotify.exe"],
        "telegram web": ["Telegram.exe", "Telegram Desktop.exe"]
    }
    
    # Приводим название к нижнему регистру для поиска
    prog_lower = program_name.lower()
    
    # Получаем список возможных имён файлов
    possible_exes = program_executables.get(prog_lower, [f"{program_name}.exe", program_name])
    
    # Ищем по всем путям
    for path in common_paths:
        if not os.path.exists(path):
            continue
            
        try:
            for root, dirs, files in os.walk(path):
                # Ограничиваем глубину поиска (чтобы не зависало)
                if root.count(os.sep) > path.count(os.sep) + 3:
                    continue
                    
                for exe_name in possible_exes:
                    for file in files:
                        if file.lower() == exe_name.lower():
                            full_path = os.path.join(root, file)
                            return full_path
        except (PermissionError, OSError):
            continue
    
    # Дополнительный поиск через where (Windows)
    try:
        result = subprocess.run(['where', program_name], capture_output=True, text=True, shell=True)
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None


def get_default_url(program_name):
    """Возвращает URL по умолчанию для популярных программ."""
    default_urls = {
        "яндекс музыка": "https://music.yandex.ru",
        "yandex music": "https://music.yandex.ru",
        "яндекс": "https://yandex.ru",
        "yandex": "https://yandex.ru",
        "google chrome": "https://www.google.com/chrome/",
        "chrome": "https://www.google.com/chrome/",
        "firefox": "https://www.mozilla.org/firefox/",
        "telegram": "https://web.telegram.org",
        "telegram desktop": "https://web.telegram.org",
        "discord": "https://discord.com/app",
        "whatsapp": "https://web.whatsapp.com",
        "zoom": "https://zoom.us/",
        "skype": "https://web.skype.com",
        "steam": "https://store.steampowered.com",
        "origin": "https://www.origin.com",
        "epic games": "https://store.epicgames.com",
        "visual studio code": "https://code.visualstudio.com",
        "vscode": "https://code.visualstudio.com",
        "редактор кода": "https://code.visualstudio.com",
        "pycharm": "https://www.jetbrains.com/pycharm/",
        "word": "https://office.com",
        "excel": "https://office.com",
        "powerpoint": "https://office.com",
        "outlook": "https://outlook.live.com",
        "spotify": "https://open.spotify.com",
        "youtube": "https://youtube.com",
        "ютуб": "https://youtube.com",
        "кинопоиск": "https://kinopoisk.ru",
        "vk": "https://vk.com",
        "вконтакте": "https://vk.com"
    }
    return default_urls.get(program_name.lower())


# ================== ОСНОВНЫЕ ФУНКЦИИ ==================

def get_user_info(key=None, **kwargs):
    """Возвращает информацию о пользователе из памяти."""
    from assistant.memory_llm import MemoryLLM
    mem = MemoryLLM()
    
    if key:
        # Поиск по конкретному ключу
        facts = mem.get_all_facts_json()
        for k, v in facts.items():
            if key.lower() in k.lower():
                return f"📌 {k}: {v}"
        
        # Если ключ не найден, предлагаем список
        all_facts = mem.recall_all_facts()
        if all_facts:
            return f"Я не знаю '{key}'. Вот что я помню:\n{all_facts}"
        return f"Я пока ничего не знаю о '{key}'. Расскажи мне."
    else:
        # Возвращаем все факты
        facts = mem.recall_all_facts()
        if facts:
            return facts
        return "Память пока пуста. Расскажи что-нибудь о себе, и я запомню."

def open_timer(seconds=60, **kwargs):
    """Открывает таймер (через системный будильник или уведомление)."""
    try:
        seconds = int(seconds)
        
        def timer_thread():
            time.sleep(seconds)
            # Показываем уведомление
            subprocess.run([
                'powershell',
                '-command',
                f'Add-Type -AssemblyName System.Windows.Forms; ' +
                f'[System.Windows.Forms.MessageBox]::Show("Время вышло!", "Таймер")'
            ])
        
        thread = threading.Thread(target=timer_thread, daemon=True)
        thread.start()
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if minutes > 0:
            time_str = f"{minutes} мин {remaining_seconds} сек"
        else:
            time_str = f"{seconds} сек"
            
        return f"✅ Таймер запущен на {time_str}"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def open_explorer(path=None):
    """Открывает проводник Windows."""
    if path is None:
        path = os.path.expanduser("~")
    try:
        subprocess.Popen(f'explorer "{path}"')
        return f"✅ Проводник открыт в папке: {path}"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def open_calculator(**kwargs):
    """Открывает калькулятор."""
    try:
        subprocess.Popen("calc.exe")
        return "✅ Калькулятор открыт"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def open_notepad(**kwargs):
    """Открывает блокнот."""
    try:
        subprocess.Popen("notepad.exe")
        return "✅ Блокнот открыт"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def open_browser(url="https://www.google.com", **kwargs):
    """Открывает браузер."""
    try:
        webbrowser.open(url)
        return f"✅ Браузер открыт с URL: {url}"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def get_time(**kwargs):
    """Возвращает текущее время."""
    now = datetime.now()
    return f"Сейчас {now.strftime('%H:%M')}"


def get_date(**kwargs):
    """Возвращает текущую дату."""
    now = datetime.now()
    return f"Сегодня {now.strftime('%d.%m.%Y')}"


def open_website(site_name=None, **kwargs):
    """Открывает популярные сайты в браузере."""
    sites = {
        "яндекс музыка": "https://music.yandex.ru",
        "хабр": "https://habr.com",
        "ютуб": "https://youtube.com",
        "гитхаб": "https://github.com",
        "гпт": "https://chat.openai.com",
        "яндекс": "https://yandex.ru",
        "гмайл": "https://mail.google.com",
        "google": "https://google.com",
        "youtube": "https://youtube.com",
        "ютуб": "https://youtube.com",
        "кинопоиск": "https://kinopoisk.ru",
        "вконтакте": "https://vk.com",
        "vk": "https://vk.com",
        "telegram": "https://web.telegram.org",
        "telegram web": "https://web.telegram.org",
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "мой сайт": "http://fieldmate.tw1.ru",
        "fieldmate": "http://fieldmate.tw1.ru",
        "филдмейт": "http://fieldmate.tw1.ru"
    }
    
    if site_name and site_name.lower() in sites:
        url = sites[site_name.lower()]
        webbrowser.open(url)
        return f"✅ Открываю {site_name}"
    elif site_name:
        if not site_name.startswith(('http://', 'https://')):
            if '.' in site_name and ' ' not in site_name:
                url = 'http://' + site_name
            else:
                url = f"https://www.google.com/search?q={site_name}"
        else:
            url = site_name
        webbrowser.open(url)
        return f"✅ Открываю {site_name}"
    else:
        return "Что открыть?"


def open_program(program_name=None, **kwargs):
    """
    Открывает программу, если она установлена.
    Если не установлена — открывает сайт в браузере.
    """
    if not program_name:
        return "Что открыть?"
    
    print(f"🔍 Ищу программу: {program_name}")
    
    # Сначала проверяем, есть ли программа
    prog_path = find_program_path(program_name)
    
    if prog_path:
        try:
            subprocess.Popen([prog_path])
            return f"✅ Открываю {program_name}"
        except Exception as e:
            return f"❌ Не удалось открыть {program_name}: {e}"
    else:
        # Программа не найдена — открываем сайт
        url = get_default_url(program_name)
        if url:
            webbrowser.open(url)
            return f"ℹ️ Программа '{program_name}' не найдена на компьютере. Открываю сайт: {url}"
        else:
            # Если нет URL по умолчанию, ищем в Google
            search_url = f"https://www.google.com/search?q={program_name}"
            webbrowser.open(search_url)
            return f"ℹ️ Программа '{program_name}' не найдена. Ищу информацию в Google: {search_url}"


# ================== СЛОВАРЬ ИНСТРУМЕНТОВ (TOOLS) ==================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_explorer",
            "description": "Открывает проводник Windows",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к папке (необязательно)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_calculator",
            "description": "Открывает калькулятор Windows. Используй ТОЛЬКО для математических расчётов, НЕ для таймеров.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_timer",
            "description": "Запускает таймер. Используй когда просят 'поставь таймер', 'засеки время', 'напомни через N минут'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "integer",
                        "description": "Количество секунд (60 = минута, 30 = полминуты)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Возвращает информацию о пользователе из памяти. Используй когда спрашивают 'как меня зовут', 'что я люблю', 'какие у меня предпочтения' и т.д.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Что именно спросить (например, 'имя', 'любит', 'профессия')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_notepad",
            "description": "Открывает простой текстовый редактор Блокнот (Notepad). Используй ТОЛЬКО для работы с простым текстом, НЕ для программирования.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_program",
            "description": "Открывает программу на компьютере. Для редакторов кода (VS Code, PyCharm и т.д.) используй ЭТУ функцию, а не open_notepad. Если программа не установлена, открывает её сайт.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program_name": {
                        "type": "string",
                        "description": "Название программы (например, 'яндекс музыка', 'telegram', 'vscode', 'редактор кода')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Показывает текущее время. Используй ТОЛЬКО когда пользователь явно спрашивает 'сколько времени', 'который час' или 'time'.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_date",
            "description": "Показывает текущую дату",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Открывает популярные сайты в браузере",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {
                        "type": "string",
                        "description": "Название сайта (например, 'яндекс музыка', 'youtube', 'мой сайт')"
                    }
                }
            }
        }
    }
]


# ================== СЛОВАРЬ ФУНКЦИЙ ==================

FUNCTIONS = {
    "open_explorer": open_explorer,
    "open_calculator": open_calculator,
    "open_notepad": open_notepad,
    "open_browser": open_browser,
    "get_time": get_time,
    "get_date": get_date,
    "open_website": open_website,
    "open_program": open_program,
    "open_timer": open_timer,
    "get_user_info": get_user_info
}