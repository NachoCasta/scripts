import requests
import shutil
import os
from time import strftime, sleep

from PIL import Image
from pytesseract import image_to_string

from robobrowser import RoboBrowser

from mail import enviar_mail

browser = RoboBrowser(history=True)


def descargar_cartas():
    browser.open('https://digital.elmercurio.com')
    paginas = browser.find_all(class_="item")
    for pagina in paginas:
        a = pagina.find("a")
        onclick = a.get("onclick")
        if onclick is None:
            continue
        args = [a.strip("'") for a in
                onclick[onclick.index("(") + 1:onclick.index(")")].split(",")]
        letter, _, number = args
        page = letter + number
        if page == "A2":
            browser.follow_link(a)
            break

    imagen = browser.find(class_="fullImg").get("src-img")
    path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    nombre = path + "/Cartas.jpg"

    r = requests.get(imagen, stream=True,
                     headers={'User-agent': 'Mozilla/5.0'})
    if r.status_code == 200:
        with open(nombre, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    return nombre


def descargar_obituarios():
    browser.open('https://digital.elmercurio.com')
    url = browser.url.replace("A", "C")
    browser.open(url)
    paginas = browser.find_all(class_="item")
    links = {}
    for pagina in paginas:
        a = pagina.find("a")
        onclick = a.get("onclick")
        if onclick is None:
            continue
        args = [a.strip("'") for a in
                onclick[onclick.index("(") + 1:onclick.index(")")].split(",")]
        letter, _, number = args
        page = letter + number
        links[page] = a
    lista = sorted(links.keys(), key=lambda k: int(k[1:]))
    for k in lista:
        browser.open(url)
        print("Pagina", k)
        browser.follow_link(links[k])
        imagen = browser.find(class_="fullImg").get("src-img")
        path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        nombre = path + "/paginas/{}.jpg".format(k)

        r = requests.get(imagen, stream=True,
                         headers={'User-agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            with open(nombre, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        if es_obituario(nombre):
            return nombre
    return None


def es_obituario(file):
    img = Image.open(file)
    for i in range(25):
        cropped = img.crop((160, 100 + 100 * i, 370, 300 + 100 * i))
        texto = image_to_string(cropped).lower().strip()
        if "obituario" in texto:
            return True
    return False


def get_mails(file):
    path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    with open(path + "/{}".format(file)) as f:
        lista = [m.strip() for m in f.readlines()]
    return lista

if __name__ == "__main__":
    cartas = descargar_cartas()
    obituarios = descargar_obituarios()
    mails_cartas = get_mails("mails.txt")
    mails_obituarios = get_mails("mails_obituarios.txt")
    for mail in mails_cartas:
        archivos = [cartas]
        if mail in mails_obituarios and obituarios is not None:
            archivos.append(obituarios)
            asunto = strftime("Cartas al director y obituario del %d/%m/%Y")
        else:
            asunto = strftime("Cartas al director del %d/%m/%Y")
        enviar_mail(mail, asunto, "", archivos)
