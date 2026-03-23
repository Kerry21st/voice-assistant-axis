"""
Консольный чат с ассистентом.
"""

from assistant.core import Assistant

def main():
    print("=" * 50)
    print("🤖 Голосовой ассистент (консольный прототип)")
    print("=" * 50)
    print("Команды: /clear - очистить историю, /exit - выход")
    print("=" * 50)
    
    assistant = Assistant()
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
            
            if user_input.lower() == "/exit":
                print("👋 До свидания!")
                break
            elif user_input.lower() == "/clear":
                assistant.clear_history()
                continue
            elif not user_input:
                continue
            
            print("🤖 Ассистент думает...")
            response = assistant.process_message(user_input)
            print(f"🤖: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Выход...")
            break

if __name__ == "__main__":
    main()