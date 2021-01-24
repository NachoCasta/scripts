import pandas as pd
import os
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

MEMORIAS = "memorias/Memorias 2019"

FIRST = "Proyectar a la Comunidad"

LAST = "Apoyo Social Indirecto"

def get_datos(path):
    datos = pd.read_excel(path)
    tabla = [[c[1], c[3], c[5]] for c in datos[5:30].values.tolist()]
    filtrado = []
    agregar = False
    for f in tabla:
        fila = f[0]
        if fila == FIRST:
            agregar = True
        if agregar:
            filtrado.append(f)
        if fila == LAST:
            agregar = False
    if not filtrado:
        print(path)
    if LAST not in filtrado[-1]:
        print(path)
        print(filtrado[-1])
        print()
    return filtrado

RESUMEN = "memorias/Congreso 2019 APORTES Datos y Graficos 2018.xlsx"

def get_regiones():
    datos = pd.read_excel(RESUMEN)
    tabla = [c[:2] for c in datos[1:194].values.tolist()]
    for f in tabla:
        print(f)
    return tabla

regiones = get_regiones()

orden_regiones = []
for (region, _) in regiones:
    if region not in orden_regiones:
        orden_regiones.append(region)

def get_region(nombre):
    return max(regiones, key=lambda k: similar(k[1], nombre))[0]

resumen = []

for file in os.listdir(MEMORIAS):
    path = f"{MEMORIAS}/{file}"
    try:
        datos = get_datos(path)
        nombre = file.split(" Mem ")[0].split("2019")[0].split("2020")[0].strip().strip("Mem")
        region = get_region(nombre)
        fila = [region, nombre]
        UF = [c[1] for c in datos]
        fila += UF
        fila.append("")
        acciones = [c[2] for c in datos]
        fila += acciones
        fila.append("")
        resumen.append(fila)
        print(region, nombre)
    except Exception as err:
        print(path)
        print(err)
        pass

resumen.sort(key=lambda k: k[1])
resumen.sort(key=lambda k: orden_regiones.index(k[0]))


labels = [c[0] for c in datos]
header = []
header.append("Región")
header.append("Círculo")
header += labels
header.append("TOTAL")
header += labels
header.append("TOTAL")

resumen = [header] + resumen

with open("memorias/resumen.csv", "w") as file:
    for fila in resumen:
        file.write(";".join(fila[:2]) + ";")
        file.write(";".join(map(str, fila[2:])).replace(".",",") + "\n")
