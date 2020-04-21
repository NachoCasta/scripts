import requests
import json

host = "https://us-central1-plataformamatpuc.cloudfunctions.net/function-1"

with open("main.tex", "r") as file:
    content = file.read()
data = {
    "files": {
        "Foto_245559.jpg": "https://firebasestorage.googleapis.com/v0/b/plataformamatpuc.appspot.com/o/-Lk1_gmMjidWHe1qE5xa%2FFoto_245559.jpg?alt=media&token=dc168336-7f99-430b-af86-70745eb47090",
        "logouc.jpg": "https://firebasestorage.googleapis.com/v0/b/plataformamatpuc.appspot.com/o/logouc.jpg?alt=media&token=d56eaeb4-13f1-4967-bd81-872739a757cc"
    },
    "content": content
}

r = requests.post(host, data=json.dumps(data))
print(r.status_code)

with open("test.pdf", "wb") as file:
    file.write(r.content)
