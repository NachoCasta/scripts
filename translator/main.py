from googletrans import Translator
translator = Translator()

with open("preguntas.txt", "r") as file:
    preguntas = [l[3:].strip() for l in file]
    print("Preguntas abiertas")

traducidas = [translator.translate(p, src="de", dest="en").text
              for p in preguntas]
print("Preguntas traducidas")

with open("traducidas.txt", "w") as file:
    for i, (p, t) in enumerate(zip(preguntas, traducidas)):
        file.write("{}. {}\n   ({})\n\n".format(i + 1, p, t))
    print("Archivo listo")
