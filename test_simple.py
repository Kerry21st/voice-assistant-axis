import requests

# Простейший запрос без tools
response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3.1:8b",
        "messages": [{"role": "user", "content": "Привет"}],
        "stream": False
    }
)

print(f"Статус: {response.status_code}")
if response.status_code == 200:
    print("✅ Успешно!")
    print(response.json())
else:
    print("❌ Ошибка:")
    print(response.text)