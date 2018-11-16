import requests, shutil
from time import strftime

from robobrowser import RoboBrowser

from mail import enviar_mail

browser = RoboBrowser(history=True)
browser.open('https://digital.elmercurio.com')

paginas = browser.find_all(class_="item")
for pagina in paginas:
    a = pagina.find("a")
    onclick = a.get("onclick")
    if onclick is None:
        continue
    args = [a.strip("'") for a in
            onclick[onclick.index("(")+1:onclick.index(")")].split(",")]
    letter, _, number = args
    page = letter + number
    if page == "A2":
        browser.follow_link(a)
        break

imagen = browser.find(class_="fullImg").get("src-img")
nombre = "Cartas.jpg"

r = requests.get(imagen, stream=True,
                 headers={'User-agent': 'Mozilla/5.0'})
if r.status_code == 200:
    with open(nombre, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

enviar_mail("icastanedaw@gmail.com",
            strftime("Cartas al director del %d/%m/%Y"), "",
            nombre)