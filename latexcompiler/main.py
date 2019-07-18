import requests
import tarfile


def compile(file_path):
    with tarfile.open("main.tar.gz", "w:gz") as tar:
        tar.add(file_path)
        tar.add("Foto_245559.jpg")
        tar.add("logouc.jpg")
    with open("main.tar.gz", "rb") as f:
        payload = {
            "command": "pdflatex",
            "target": file_path
        }
        files = {
            "file": f
        }
        host = "https://latexonline.cc/data"
        r = requests.post(host, params=payload, files=files)
    with open("result.pdf", 'wb') as fd:
        fd.write(r.content)

if __name__ == "__main__":
    compile("main.tex")
