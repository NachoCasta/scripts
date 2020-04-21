import calendar
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import base64

try:
    import Tkinter
    import tkFont
except ImportError: # py3k
    import tkinter as Tkinter
    import tkinter.font as tkFont

from tkinter import ttk

def get_calendar(locale, fwday):
    # instantiate proper calendar class
    if locale is None:
        return calendar.TextCalendar(fwday)
    else:
        return calendar.LocaleTextCalendar(fwday, locale)

class Calendar(ttk.Frame):
    # XXX ToDo: cget and configure

    datetime = calendar.datetime.datetime
    timedelta = calendar.datetime.timedelta

    def __init__(self, master=None, **kw):
        """
        WIDGET-SPECIFIC OPTIONS
            locale, firstweekday, year, month, selectbackground,
            selectforeground
        """
        # remove custom options from kw before initializating ttk.Frame
        fwday = kw.pop('firstweekday', calendar.MONDAY)
        year = kw.pop('year', self.datetime.now().year)
        month = kw.pop('month', self.datetime.now().month)
        locale = kw.pop('locale', None)
        sel_bg = kw.pop('selectbackground', '#ecffc4')
        sel_fg = kw.pop('selectforeground', '#05640e')

        self._date = self.datetime(year, month, 1)
        self._selection = None # no date selected

        ttk.Frame.__init__(self, master, **kw)

        self._cal = get_calendar(locale, fwday)

        self.__setup_styles()       # creates custom styles
        self.__place_widgets()      # pack/grid used widgets
        self.__config_calendar()    # adjust calendar columns and setup tags
        # configure a canvas, and proper bindings, for selecting dates
        self.__setup_selection(sel_bg, sel_fg)

        # store items ids, used for insertion later
        self._items = [self._calendar.insert('', 'end', values='')
                            for _ in range(6)]
        # insert dates in the currently empty calendar
        self._build_calendar()

    def __setitem__(self, item, value):
        if item in ('year', 'month'):
            raise AttributeError("attribute '%s' is not writeable" % item)
        elif item == 'selectbackground':
            self._canvas['background'] = value
        elif item == 'selectforeground':
            self._canvas.itemconfigure(self._canvas.text, item=value)
        else:
            ttk.Frame.__setitem__(self, item, value)

    def __getitem__(self, item):
        if item in ('year', 'month'):
            return getattr(self._date, item)
        elif item == 'selectbackground':
            return self._canvas['background']
        elif item == 'selectforeground':
            return self._canvas.itemcget(self._canvas.text, 'fill')
        else:
            r = ttk.tclobjs_to_py({item: ttk.Frame.__getitem__(self, item)})
            return r[item]

    def __setup_styles(self):
        # custom ttk styles
        style = ttk.Style(self.master)
        arrow_layout = lambda dir: (
            [('Button.focus', {'children': [('Button.%sarrow' % dir, None)]})]
        )
        style.layout('L.TButton', arrow_layout('left'))
        style.layout('R.TButton', arrow_layout('right'))

    def __place_widgets(self):
        # header frame and its widgets
        hframe = ttk.Frame(self)
        lbtn = ttk.Button(hframe, style='L.TButton', command=self._prev_month)
        rbtn = ttk.Button(hframe, style='R.TButton', command=self._next_month)
        self._header = ttk.Label(hframe, width=15, anchor='center')
        # the calendar
        self._calendar = ttk.Treeview(self, show='', selectmode='none', height=7)

        # pack the widgets
        hframe.pack(in_=self, side='top', pady=4, anchor='center')
        lbtn.grid(in_=hframe)
        self._header.grid(in_=hframe, column=1, row=0, padx=12)
        rbtn.grid(in_=hframe, column=2, row=0)
        self._calendar.pack(in_=self, expand=1, fill='both', side='bottom')

    def __config_calendar(self):
        cols = self._cal.formatweekheader(3).split()
        self._calendar['columns'] = cols
        self._calendar.tag_configure('header', background='grey90')
        self._calendar.insert('', 'end', values=cols, tag='header')
        # adjust its columns width
        font = tkFont.Font()
        maxwidth = max(font.measure(col) for col in cols)
        for col in cols:
            self._calendar.column(col, width=maxwidth, minwidth=maxwidth,
                anchor='e')

    def __setup_selection(self, sel_bg, sel_fg):
        self._font = tkFont.Font()
        self._canvas = canvas = Tkinter.Canvas(self._calendar,
            background=sel_bg, borderwidth=0, highlightthickness=0)
        canvas.text = canvas.create_text(0, 0, fill=sel_fg, anchor='w')

        canvas.bind('<ButtonPress-1>', lambda evt: canvas.place_forget())
        self._calendar.bind('<Configure>', lambda evt: canvas.place_forget())
        self._calendar.bind('<ButtonPress-1>', self._pressed)

    def __minsize(self, evt):
        width, height = self._calendar.master.geometry().split('x')
        height = height[:height.index('+')]
        self._calendar.master.minsize(width, height)

    def _build_calendar(self):
        year, month = self._date.year, self._date.month

        # update header text (Month, YEAR)
        header = self._cal.formatmonthname(year, month, 0)
        self._header['text'] = header.title()

        # update calendar shown dates
        cal = self._cal.monthdayscalendar(year, month)
        for indx, item in enumerate(self._items):
            week = cal[indx] if indx < len(cal) else []
            fmt_week = [('%02d' % day) if day else '' for day in week]
            self._calendar.item(item, values=fmt_week)

    def _show_selection(self, text, bbox):
        """Configure canvas for a new selection."""
        x, y, width, height = bbox

        textw = self._font.measure(text)

        canvas = self._canvas
        canvas.configure(width=width, height=height)
        canvas.coords(canvas.text, width - textw, height / 2 - 1)
        canvas.itemconfigure(canvas.text, text=text)
        canvas.place(in_=self._calendar, x=x, y=y)

    # Callbacks

    def _pressed(self, evt):
        """Clicked somewhere in the calendar."""
        x, y, widget = evt.x, evt.y, evt.widget
        item = widget.identify_row(y)
        column = widget.identify_column(x)

        if not column or not item in self._items:
            # clicked in the weekdays row or just outside the columns
            return

        item_values = widget.item(item)['values']
        if not len(item_values): # row is empty for this month
            return

        text = item_values[int(column[1]) - 1]
        if not text: # date is empty
            return

        bbox = widget.bbox(item, column)
        if not bbox: # calendar not visible yet
            return

        # update and then show selection
        text = '%02d' % text
        self._selection = (text, item, column)
        self._show_selection(text, bbox)

    def _prev_month(self):
        """Updated calendar to show the previous month."""
        self._canvas.place_forget()

        self._date = self._date - self.timedelta(days=1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self._build_calendar() # reconstuct calendar

    def _next_month(self):
        """Update calendar to show the next month."""
        self._canvas.place_forget()

        year, month = self._date.year, self._date.month
        self._date = self._date + self.timedelta(
            days=calendar.monthrange(year, month)[1] + 1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self._build_calendar() # reconstruct calendar

    # Properties

    @property
    def selection(self):
        """Return a datetime representing the current selected date."""
        if not self._selection:
            return None

        year, month = self._date.year, self._date.month
        return self.datetime(year, month, int(self._selection[0]))


from tkinter import *
from tkinter.ttk import *

class Dialog(Toplevel):
    """Sourced from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm"""
    def __init__(self, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override


import tkinter as Tkinter

class CalendarDialog(Dialog):
    """Dialog box that displays a calendar and returns the selected date"""
    def body(self, master):
        self.calendar = Calendar(master)
        self.calendar.pack()

    def apply(self):
        self.result = self.calendar.selection

import sqlite3
import os
import smtplib
import string
import _thread
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from time import sleep, strftime
from datetime import datetime

class Paciente:

    def __init__(
        self, nombre, apellido, nombre_apoderado="", apellido_apoderado="",
        mail="", telefono="", direccion=""):
        def mayus(s):
            if len(s) > 0: return s[0].upper() + s[1:].lower()
            else: return ""
        self.nombre = " ".join(mayus(s) for s in nombre.split())
        self.apellido = " ".join(mayus(s) for s in apellido.split())
        self.nombre_apoderado = mayus(nombre_apoderado)
        self.apellido_apoderado = mayus(apellido_apoderado)
        self.mail = mail
        self.telefono = telefono
        self.direccion = direccion
        self.sesiones = []

    def __repr__(self):
        return self.apellido + " " + self.nombre

    def __lt__(self, other):
        return self.apellido + self.nombre < other.apellido + other.nombre

    def __eq__(self, other):
        return self.nombre == other.nombre and self.apellido == other.apellido

    def get_nombre(self):
        return self.nombre + " " + self.apellido

    def get_nombre_apoderado(self):
        return self.nombre_apoderado + " " + self.apellido_apoderado

    def agregar_sesion(self, dia, mes, ano, valor, comentario=""):
        sesion = Sesion(dia, mes, ano, valor, comentario)
        self.sesiones.append(sesion)
        self.sesiones.sort(reverse=True)

    def eliminar_sesion(self, sesion):
        self.sesiones.remove(sesion)


class Sesion:

    def __init__(self, dia, mes, ano, valor, comentario=""):
        self.dia = str(dia).zfill(2)
        self.mes = str(mes).zfill(2)
        self.ano = str(ano).zfill(4)
        self.valor = valor
        self.comentario = comentario

    def __repr__(self):
        return "/".join((self.dia, self.mes, self.ano)) + \
               " - " + str(self.valor)

    def __lt__(self, other):
        return "".join((self.ano, self.mes, self.dia)) < \
               "".join((other.ano, other.mes, other.dia))

    def get_fecha(self):
        return self.dia+"/"+self.mes+"/"+self.ano

            
class ListaPacientes:

    def __init__(self, archivo="pacientes.db"):
        self.pacientes = []
        self.root = Tk()
        self.db_path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isfile(self.db_path+"/"+archivo):
            with sqlite3.connect(archivo) as file:
                db = file.cursor()
                db.execute("""CREATE TABLE datos
                    (nombre, apellido, nombre_apoderado, apellido_apoderado,
                     mail, telefono, direccion)""")
        self.cargar(archivo)
        self.GUI()
                
    def __repr__(self):
        return "\n".join(map(str,self.pacientes))

    def guardar(self, archivo="pacientes.db"):
        if not os.path.isfile(self.db_path+"/"+archivo):
            with sqlite3.connect(archivo) as file:
                db = file.cursor()
                db.execute("""CREATE TABLE datos
                    (nombre, apellido, nombre_apoderado, apellido_apoderado,
                     mail, telefono, direccion)""")
        with sqlite3.connect(archivo) as file:
            db = file.cursor()
            db.execute("DELETE FROM datos")
            pacientes = [
                (p.nombre, p.apellido, p.nombre_apoderado, p.apellido_apoderado,
                 p.mail, p.telefono, p.direccion) for p in self.pacientes]
            db.executemany("INSERT INTO datos VALUES (?,?,?,?,?,?,?)",
                           pacientes)
            for p in self.pacientes:
                db.execute("CREATE TABLE IF NOT EXISTS " + limpiar(str(p)) +
                           "(fecha, valor, comentario)")
                db.execute("DELETE FROM " + limpiar(str(p)))
                for s in p.sesiones:
                    fecha = "/".join((s.ano, s.mes, s.dia))
                    db.execute("INSERT INTO " + limpiar(str(p)) +
                               " VALUES (?,?,?)", (fecha, s.valor, s.comentario))
                
    def cargar(self, archivo="pacientes.db"):
        with sqlite3.connect(archivo) as file:
            db = file.cursor()
            for p in db.execute("SELECT * FROM datos ORDER BY apellido"):
                self.agregar_paciente(p[0], p[1], p[2], p[3], p[4], p[5], p[6])
            for p in self.pacientes:
                for fecha, valor, comentario in db.execute(
                    "SELECT * FROM " +  limpiar(str(p)) + " ORDER BY fecha"):
                    ano, mes, dia = fecha.split("/")
                    p.agregar_sesion(dia, mes, ano, valor, comentario)

    def agregar_paciente(
        self, nombre, apellido, nombre_apoderado="", apellido_apoderado="",
        mail="", telefono="", direccion=""):
        "Agrega un paciente a la lista de pacientes"
        paciente = Paciente(
            nombre, apellido, nombre_apoderado, apellido_apoderado,
            mail, telefono, direccion)
        self.pacientes.append(paciente)
        self.pacientes.sort()

    def eliminar_paciente(self, paciente, archivo="pacientes.db"):
        if paciente in self.pacientes:
            self.pacientes.remove(paciente)
            self.guardar()
        

    def buscar_paciente(self, apellido_nombre):
        try:
            indice = list(map(str, self.pacientes)).index(apellido_nombre)
            return self.pacientes[indice]
        except ValueError:
            return Paciente("", "")

    def buscar_sesion(self, paciente, str_sesion):
        try:
            indice = list(map(str, paciente.sesiones)).index(str_sesion)
            return paciente.sesiones[indice]
        except ValueError:
            return Sesion("", "", "", 0)
    
    def sesiones(self, paciente, mes, ano):
        s = ""
        comentarios = "\n"
        total = 0
        for sesion in paciente.sesiones:
            if int(sesion.mes) != mes or int(sesion.ano) != ano:
                continue
            total += sesion.valor
            s += "{0}/{1}/{2}{3: >10}".format(
                sesion.dia, sesion.mes, sesion.ano, "$ " + str(sesion.valor))
            s += "\n"
            if sesion.comentario != "":
                comentarios += "\n" + sesion.get_fecha() + \
                               " - " + sesion.comentario
        s += "\n" + "{0: <10}{1: >10}".format("Total:", "$ " + str(total))
        s += comentarios
        return s

    def GUI(self):

        def update_meses():
            meses_dict = {
                "01":"Enero", "02":"Febrero", "03":"Marzo",
                "04":"Abril", "05":"Mayo", "06":"Junio",
                "07":"Julio", "08":"Agosto", "09":"Septiembre",
                "10":"Octubre", "11":"Noviembre", "12":"Diciembre"}
            meses_inv = {v:k for k, v in meses_dict.items()}
            meses = []
            for p in self.pacientes:
                for s in p.sesiones:
                    if s.ano+s.mes < strftime("%Y%m"):
                        meses.append(meses_dict[s.mes]+" de "+s.ano)
            meses = list(set(meses))
            meses.sort(key=lambda k: k.split()[2]+meses_inv[k.split()[0]],
                       reverse=True)
            lista_meses["values"] = meses

        def update_meses_info(n, m, x):
            progress_bar["value"] = 0
            info_correo.set("")

        def mail_mensual():
            meses_inv = {'Marzo': '03', 'Octubre': '10', 'Julio': '07',
                         'Abril': '04', 'Mayo': '05', 'Diciembre': '12',
                         'Enero': '01', 'Junio': '06', 'Septiembre': '09',
                         'Agosto': '08', 'Febrero': '02', 'Noviembre': '11'}
            mes_actual = meses.get()
            mes = int(meses_inv[mes_actual.split()[0]])
            ano = int(mes_actual.split()[2])
            contador = 0
            total = 0
            for i, paciente in enumerate(self.pacientes):
                progress_bar["value"] = (100*i/(len(self.pacientes)))
                sesiones = [s for s in paciente.sesiones
                            if int(s.mes) == mes and int(s.ano) == ano]
                if not sesiones:
                    continue
                info_correo.set(paciente.get_nombre())
                total += 1
                nombre = paciente.get_nombre_apoderado()
                nombre_a = paciente.get_nombre()
                mensaje = "Estimad@ " + nombre + ":\n\n"
                mensaje += "Sesiones de " + nombre_a + \
                           " en el mes de " + mes_actual + ":\n\n"
                mensaje += self.sesiones(paciente, mes, ano)
                mensaje += "\n\n"
                mensaje += "Datos de transferencia:\n\n"
                mensaje += "Marcela Kleinknecht Luer\n"
                mensaje += "Banco de Chile\n"
                mensaje += "Cuenta: 000-05769-10\n"
                mensaje += "Rut: 9.615.431-3\n"
                mensaje += "marcelakleinknecht132@gmail.com\n"
                mensaje += "\n\n"
                mensaje += "Atte. Graciela Almagia\n"
                mensaje += "Secretaria"
                mail = paciente.mail
                asunto = "Sesiones del mes de " + mes_actual
                try:
                    if mail != "":
                        send(mail, asunto, mensaje)
                        contador += 1
                    else:
                        raise Exception("No hay mail")
                except Exception as err:
                    info_correo.set("Error: {}".format(paciente.get_nombre()))
                    alternativo = "marcelaklein@yahoo.es"
                    send(alternativo, asunto, mensaje)
                progress_bar["value"] = (100*i/(len(self.pacientes)-1))
            progress_bar["value"] = 100
            info_correo.set("Enviados {}/{}".format(contador, total))
                
        
        def update_pacientes():
            lista_pacientes["values"] = list(map(str, self.pacientes))
            lista_sesiones["values"] = []

        def update_sesiones():
            paciente = self.buscar_paciente(pacientes.get())
            lista_sesiones["values"] = list(map(str, paciente.sesiones))

        def update_pacientes_datos(n, m, x):
            paciente = self.buscar_paciente(pacientes.get())
            nombre.set(paciente.nombre)
            apellido.set(paciente.apellido)
            nombre_apoderado.set(paciente.nombre_apoderado)
            apellido_apoderado.set(paciente.apellido_apoderado)
            mail.set(paciente.mail)
            telefono.set(paciente.telefono)
            direccion.set(paciente.direccion)
            if paciente.sesiones:
                sesiones.set(str(paciente.sesiones[0]))
            else:
                sesiones.set("")
            guardar_info.set("")
            guardar_info2.set("")
            
        def update_sesiones_datos(n, m, x):
            paciente = self.buscar_paciente(pacientes.get())
            sesion = self.buscar_sesion(paciente, sesiones.get())
            fecha.set("/".join([sesion.dia, sesion.mes, sesion.ano]))
            valor.set(sesion.valor)
            comentario.set(sesion.comentario)
            guardar_info2.set("")

        def agregar_nuevo_paciente():
            self.agregar_paciente("Paciente Nuevo", "")
            p = self.buscar_paciente(" Paciente Nuevo")
            pacientes.set(str(p))

        def agregar_nueva_sesion():
            paciente = self.buscar_paciente(pacientes.get())
            now = datetime.now()
            paciente.agregar_sesion(now.day, now.month, now.year, 0)
            sesiones.set(strftime("%d/%m/%Y")+" - 0")

        def modificar_paciente():
            paciente = self.buscar_paciente(pacientes.get())
            paciente.nombre = nombre.get()
            paciente.apellido = apellido.get()
            paciente.nombre_apoderado = nombre_apoderado.get()
            paciente.apellido_apoderado = apellido_apoderado.get()
            paciente.mail = mail.get()
            paciente.telefono = telefono.get()
            paciente.direccion = direccion.get()
            pacientes.set(str(paciente))
            guardar_info.set("Cambios guardados!")
            self.guardar()

        def modificar_sesion():
            paciente = self.buscar_paciente(pacientes.get())
            sesion = self.buscar_sesion(paciente, sesiones.get())
            dia, mes, ano = fecha.get().split("/")
            sesion.dia = dia
            sesion.mes = mes
            sesion.ano = ano
            sesion.valor = valor.get()
            sesion.comentario = comentario.get()
            sesiones.set(str(sesion))
            paciente.sesiones.sort(reverse=True)
            self.guardar()
            guardar_info2.set("Cambios guardados!")

        def eliminar_paciente():
            paciente = self.buscar_paciente(pacientes.get())
            result = messagebox.askquestion(
                "Eliminar paciente",
                "¿Estas seguro que deseas eliminar a " + paciente.get_nombre() +
                "?", icon='warning')
            if result == 'yes':
                self.eliminar_paciente(paciente)
                guardar_info.set("Paciente eliminado")
                pacientes.set("")

        def eliminar_sesion():
            paciente = self.buscar_paciente(pacientes.get())
            sesion = self.buscar_sesion(paciente, sesiones.get())
            result = messagebox.askquestion(
                "Eliminar sesión",
                "¿Estas seguro que deseas eliminar la sesión?", icon='warning')
            if result == 'yes':
                paciente.eliminar_sesion(sesion)
                self.guardar()
                guardar_info2.set("Sesión eliminada")
                sesiones.set("")

        def get_fecha():
            cd = CalendarDialog(c3_fila2)
            result = cd.result
            if result:
                fecha.set(result.strftime("%d/%m/%Y"))
        
        # Main frames
        self.root.title("Asistencia")
        main_frame = MyFrame(self.root)
        cuerpo1 = MyLabelFrame(main_frame, c=1, r=1,
                               t="E-Mail mensual", rel="groove")
        cuerpo2 = MyLabelFrame(main_frame, c=1, r=2, t="Paciente", rel="groove")
        cuerpo3 = MyLabelFrame(main_frame, c=1, r=3, t="Sesión", rel="groove")

        # Cuerpo 1 - E-Mail mensual
        #       Lista
        c1_fila1 = MyFrame(cuerpo1, c=1, r=1)
        meses = StringVar()
        meses.trace("w", update_meses_info)
        mes_label = Label(
            c1_fila1, text="Mes", anchor=W, width=8
            ).grid(column=1, row=1)
        lista_meses = ttk.Combobox(
            c1_fila1,
            values=[],
            textvariable=meses, width=24,
            postcommand=update_meses
            ); lista_meses.grid(column=2, row=1)
        enviar_mail_button = ttk.Button(
            c1_fila1,
            text="Enviar",
            command=lambda: _thread.start_new_thread(
                mail_mensual, ())
            ).grid(column=3, row=1)
        c1_fila1.pad(x=6,y=0)
        #       Info
        c1_fila2 = MyFrame(cuerpo1, c=1, r=2)
        progress_bar = ttk.Progressbar(
            c1_fila2, length=170, value=0
            ); progress_bar.grid(column=1, row=1)
        info_correo = StringVar()
        info_correo_label = Label(
            c1_fila2, textvariable=info_correo, width=20
            ).grid(column=2, row=1)
        c1_fila2.pad(y=0)
        
        # Cuerpo 2 - Paciente
        #       Lista
        c2_fila1 = MyFrame(cuerpo2, c=1, r=1)
        pacientes = StringVar()
        pacientes.trace("w", update_pacientes_datos)
        pacientes_label = Label(
            c2_fila1, text="Pacientes", anchor=W, width=8
            ).grid(column=1, row=1)
        lista_pacientes = ttk.Combobox(
            c2_fila1,
            values=[],
            textvariable=pacientes, width=24,
            postcommand=update_pacientes
            ); lista_pacientes.grid(column=2, row=1)
        nuevo_paciente_button = ttk.Button(
            c2_fila1,
            text="Agregar",
            command=agregar_nuevo_paciente
            ).grid(column=3, row=1)
        c2_fila1.pad(y=0)
        c2_fila1.columnconfigure(1,weight=1)
        c2_fila1.columnconfigure(2,weight=3)
        #       Paciente
        c2_fila2 = MyLabelFrame(cuerpo2, t="Datos paciente",
                                c=1, r=2, rel="groove")
        nombre = StringVar()
        nombre_label = Label(
            c2_fila2, text="Nombre", width=7, anchor=W
            ).grid(column=1, row=1)
        nombre_entry = ttk.Entry(
            c2_fila2, textvariable=nombre, width=15
            ).grid(column=2, row=1)
        apellido = StringVar()
        apellido_label = Label(
            c2_fila2, text="Apellido", width=7, anchor=W
            ).grid(column=3, row=1)
        apellido_entry = ttk.Entry(
            c2_fila2, textvariable=apellido, width=15
            ).grid(column=4, row=1)
        c2_fila2.pad()
        #       Apoderado
        c2_fila3 = MyLabelFrame(cuerpo2, t="Datos apoderado",
                                c=1, r=3, rel="groove",
                                p="0 0 0 0")
        c2_fila3_1 = MyFrame(c2_fila3, c=1, r=1, p="3 3 12 6")
        nombre_apoderado = StringVar()
        nombre_apoderado_label = Label(
            c2_fila3_1, text="Nombre", width=7, anchor=W
            ).grid(column=1, row=1)
        nombre_apoderado_entry = ttk.Entry(
            c2_fila3_1, textvariable=nombre_apoderado, width=15
            ).grid(column=2, row=1)
        apellido_apoderado = StringVar()
        apellido_apoderado_label = Label(
            c2_fila3_1, text="Apellido", width=7, anchor=W
            ).grid(column=3, row=1)
        apellido_apoderado_entry = ttk.Entry(
            c2_fila3_1, textvariable=apellido_apoderado, width=15
            ).grid(column=4, row=1)
        mail = StringVar()
        mail_label = Label(
            c2_fila3_1, text="Mail", width=7, anchor=W
            ).grid(column=1, row=2)
        mail_entry = ttk.Entry(
            c2_fila3_1, textvariable=mail, width=15
            ).grid(column=2, row=2)
        telefono = StringVar()
        telefono_label = Label(
            c2_fila3_1, text="Teléfono", width=7, anchor=W
            ).grid(column=3, row=2)
        telefono_entry = ttk.Entry(
            c2_fila3_1, textvariable=telefono, width=15
            ).grid(column=4, row=2)
        c2_fila3_1.pad()
        c2_fila3_2 = MyFrame(c2_fila3, c=1, r=2, p="3 0 12 12", sti=W)
        direccion = StringVar()
        direccion_label = Label(
            c2_fila3_2, text="Dirección", anchor=W, width=7
            ).grid(column=1, row=1)
        direccion_entry = ttk.Entry(
            c2_fila3_2, textvariable=direccion, width=43
            ).grid(column=2, row=1)
        c2_fila3_2.columnconfigure(1,weight=1)
        c2_fila3_2.columnconfigure(2,weight=3)
        c2_fila3_2.pad(y=0)
        c2_fila3.pad(x=0, y=0)
        #       Guardar
        c2_fila4 = MyFrame(cuerpo2, c=1, r=4, sti=W)
        guardar_paciente_button = ttk.Button(
            c2_fila4,
            text="Guardar cambios",
            command=modificar_paciente
            ).grid(column=1, row=1)
        guardar_info = StringVar()
        guardar_info_label = Label(
            c2_fila4, textvariable=guardar_info, anchor=W, width=19
            ).grid(column=2, row=1)
        eliminar_paciente_button = ttk.Button(
            c2_fila4,
            text="Eliminar",
            command=eliminar_paciente
            ).grid(column=3, row=1)
        c2_fila4.pad(y=0)
        
        # Cuerpo 3 - Sesion
        #       Lista
        c3_fila1 = MyFrame(cuerpo3, c=1, r=1)
        sesiones = StringVar()
        sesiones.trace("w", update_sesiones_datos)
        sesiones_label = Label(
            c3_fila1, text="Lista de sesiones", anchor=W, width=14
            ).grid(column=1, row=1)
        lista_sesiones = ttk.Combobox(
            c3_fila1,
            values=[],
            textvariable=sesiones, width=18,
            postcommand=update_sesiones
            ); lista_sesiones.grid(column=2, row=1)
        nueva_sesion_button = ttk.Button(
            c3_fila1,
            text="Agregar",
            command=agregar_nueva_sesion
            ).grid(column=3, row=1)
        c3_fila1.pad(y=0)
        c3_fila1.columnconfigure(1,weight=1)
        c3_fila1.columnconfigure(2,weight=3)
        #       Sesion
        c3_fila2 = MyLabelFrame(cuerpo3, t="Datos sesion", sti=W,
                                c=1, r=2, rel="groove", p="3 3 12 12")
        fecha = StringVar()
        Button(c3_fila2, text="Fecha...", command=get_fecha, width=10
               ).grid(column=1, row=1)
        Label(c3_fila2, textvariable=fecha, width=10
              ).grid(column=2, row=1)
        valor = IntVar(value=0)
        valor_label = Label(
            c3_fila2, text=" "*18+"Valor", anchor=E
            ).grid(column=3, row=1)
        valor_entry = ttk.Entry(
            c3_fila2, textvariable=valor, width=6
            ).grid(column=4, row=1)
        c3_fila2.pad(x=7)

        c3_fila3 = MyFrame(cuerpo3, c=1, r=3, sti=W)
        comentario = StringVar()
        comentario_label = Label(
            c3_fila3, text="Comentario", anchor=W, width=10
            ).grid(column=1, row=1)
        comentario_entry = ttk.Entry(
            c3_fila3, textvariable=comentario, width=40
            ).grid(column=2, row=1)
        c3_fila3.pad()
        #       Guardar
        c3_fila4 = MyFrame(cuerpo3, c=1, r=4, sti=W)
        guardar_paciente_button = ttk.Button(
            c3_fila4,
            text="Guardar cambios",
            command=modificar_sesion
            ).grid(column=1, row=1)
        guardar_info2 = StringVar()
        guardar_info2_label = Label(
            c3_fila4, textvariable=guardar_info2, anchor=W, width=19
            ).grid(column=2, row=1)
        eliminar_paciente_button = ttk.Button(
            c3_fila4,
            text="Eliminar",
            command=eliminar_sesion
            ).grid(column=3, row=1)
        c3_fila4.pad(y=0)
        #
        cuerpo1.pad(y=0); cuerpo2.pad(); cuerpo3.pad()
        main_frame.pad()
        self.root.mainloop()
    

class MyFrame(ttk.Frame):
    "Default Frame class"
    
    def __init__(self, master, c=0, r=0, rel=None,
                 sti=(N,W,E,S), p="3 3 12 12"):
        super(MyFrame, self).__init__(master, padding=p, relief=rel)
        self.grid(column=c,row=r,sticky=sti)
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

    def pad(self, x=5, y=3):
        for child in self.winfo_children():
            child.grid_configure(padx=x, pady=y)

class MyLabelFrame(ttk.LabelFrame):
    "Default Frame class"
    
    def __init__(self, master, t=None, c=0, r=0, rel=None,
                 sti=(N,W,E,S), p="3 3 12 12"):
        super(MyLabelFrame, self).__init__(master, text=t, padding=p, relief=rel)
        self.grid(column=c,row=r,sticky=sti)
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

    def pad(self, x=5, y=3):
        for child in self.winfo_children():
            child.grid_configure(padx=x, pady=y)

        
def limpiar(nombre_tabla):
    return ''.join(car for car in nombre_tabla if car.isalnum())

##def send(mail, asunto, mensaje):
##    "Sends e-mail"
##    
##    msg = "\r\n".join([
##        "From: mangadescarga@gmail.com",#marcelakleinknecht132@gmail.com",
##        "To: "+mail,
##        "Subject: "+asunto,
##        "",
##        mensaje
##        ])
##    fromaddr = "mangadescarga@gmail.com"#"marcelakleinknecht132@gmail.com"
##    toaddr = mail
##    username = "mangadescarga@gmail.com"#"marcelakleinknecht132"
##    password = "manga140100"#"fonoaudiologa"
##    server = smtplib.SMTP("smtp.gmail.com:587")
##    server.ehlo()
##    server.starttls()
##    server.login(username,password)
##    server.sendmail(fromaddr,toaddr,msg)
##    server.quit()

def send(destinatario, asunto, mensaje, files=[]):
    if type(destinatario) != list:
        destinatario = [destinatario]
    if type(files) != list:
        files = [files]
    msg = MIMEMultipart()
    msg['From'] = "Marcela Kleinknecht"
    msg['To'] = COMMASPACE.join(destinatario)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = asunto

    msg.attach(MIMEText(mensaje))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
            part['Content-Disposition'] = (
                'attachment; filename="%s"' % basename(f))
            msg.attach(part)
            
    fromaddr = "marcelakleinknecht132@gmail.com"
    toaddr = destinatario
    username = "marcelakleinknecht132@gmail.com"
    password = "fonoaudiologa"
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr,toaddr,msg.as_string())
    server.quit()

def to_ascii(s):
    p = set(string.printable)
    return "".join(filter(lambda k: k in p, s))

l = ListaPacientes()
