import requests
import tarfile
import os
import json
from flask import send_file


def compile(request):
    data = json.loads(request.data)
    if not os.path.exists("/tmp/files"):
        os.mkdir("/tmp/files")
    with open("/tmp/files/main.tex", "w") as file:
        file.write(data["content"])
    for name, url in data["files"].items():
        with open("/tmp/files/" + name, "wb") as file:
            response = requests.get(url, stream=True)
            for block in response.iter_content(1024):
                if not block:
                    break
                file.write(block)
    with tarfile.open("/tmp/main.tar.gz", "w:gz") as tar:
        for file in os.listdir("/tmp/files"):
            tar.add("/tmp/files/" + file, file)
    with open("/tmp/main.tar.gz", "rb") as f:
        payload = {
            "command": "pdflatex",
            "target": "main.tex"
        }
        files = {
            "file": f
        }
        host = "https://latexonline.cc/data"
        r = requests.post(host, params=payload, files=files)
    with open("/tmp/output.pdf", 'wb') as fd:
        print(r.status_code)
        fd.write(r.content)
    os.remove("/tmp/main.tar.gz")
    for file in os.listdir("/tmp/files"):
        os.remove("/tmp/files/" + file)
    os.rmdir("/tmp/files")
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }
    return (send_file("/tmp/output.pdf"), 200, headers)


class Request:

    def __init__(self, data):
        self.data = json.dumps(data)


if __name__ == "__main__":
    with open("main.tex", "r") as file:
        content = file.read()
    data = {
        "files": {
            "Foto_245559.jpg": "https://firebasestorage.googleapis.com/v0/b/plataformamatpuc.appspot.com/o/-Lk1_gmMjidWHe1qE5xa%2FFoto_245559.jpg?alt=media&token=dc168336-7f99-430b-af86-70745eb47090",
            "logouc.jpg": "https://firebasestorage.googleapis.com/v0/b/plataformamatpuc.appspot.com/o/logouc.jpg?alt=media&token=d56eaeb4-13f1-4967-bd81-872739a757cc"
        },
        "content": content
    }
    request = Request(data)
    compile(request)
