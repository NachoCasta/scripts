import requests
import tarfile
import os


def compile(folder, target):
    with tarfile.open("main.tar.gz", "w:gz") as tar:
        for file in os.listdir(folder):
            tar.add(folder + "/" + file, file)
    with open("main.tar.gz", "rb") as f:
        payload = {
            "command": "pdflatex",
            "target": target
        }
        files = {
            "file": f
        }
        host = "https://latexonline.cc/data"
        r = requests.post(host, params=payload, files=files)
    with open("output.pdf", 'wb') as fd:
        print(r.status_code)
        fd.write(r.content)
    os.remove("main.tar.gz")


if __name__ == "__main__":
    compile("files", "main.tex")
