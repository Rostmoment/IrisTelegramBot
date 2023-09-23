import json
import os
import pyperclip
text = input("Введите текст для конвертиации: ")
data = {
    "text": text
}
data = json.dumps(data, indent=4)
with open("converted.json", "w") as fh:
    fh.write(data)
with open("converted.json", "r") as fh:
    data = fh.read()
data = data.replace("{\n    \"text\": ", "").replace("}", "")
os.remove("converted.json")
with open("converted.txt", "w") as fh:
    fh.write(data)
pyperclip.copy(data)
print(f"{data}\nТекст сохранен в converted.txt\nТекст сохранен в буфер обмена!")