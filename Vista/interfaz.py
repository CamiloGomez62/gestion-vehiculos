import sqlite3
from tkinter import TclError, messagebox, ttk

import customtkinter as ctk

from controlador.controlador import ControladorPrincipal

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Campos propios de cada tipo de vehículo: (clave, etiqueta, widget, opciones)
CAMPOS_DETALLE = {
    "Auto": [
        ("puertas", "Puertas:", "entry", "Ej. 4"),
        ("combustible", "Combustible:", "menu",
         ["Gasolina", "Diésel", "Híbrido", "Eléctrico", "Gas"]),
        ("camara", "Cámara reversa:", "menu", ["Sí", "No"]),
    ],
    "Moto": [
        ("cilindraje", "Cilindraje (cc):", "entry", "Ej. 250"),
        ("manubrio", "Manubrio:", "menu",
         ["Deportivo", "Naked", "Crucero", "Touring", "Cross"]),
        ("abs", "Frenos ABS:", "menu", ["Sí", "No"]),
    ],
    "Camión": [
        ("carga", "Capacidad (Ton):", "entry", "Ej. 10.5"),
        ("ejes", "Número de ejes:", "entry", "Ej. 2"),
        ("carroceria", "Carrocería:", "menu",
         ["Estacas", "Furgón", "Volqueta", "Tanque", "Plataforma"]),
    ],
}

# Columnas de la tabla según la vista: (título, ancho)
COLS_INVENTARIO = [
    ("VIN", 76), ("Marca", 66), ("Modelo", 70), ("Año", 42), ("Tipo", 64),
    ("Precio", 86), ("Estado", 78), ("Detalle", 150),
]
COLS_DISPONIBLES = [
    ("VIN", 100), ("Marca", 105), ("Modelo", 115), ("Año", 60), ("Tipo", 90),
    ("Precio Base", 150),
]
COLS_VENTAS = [
    ("ID", 56), ("VIN", 70), ("Vehículo", 100), ("Cliente", 100),
    ("Teléfono", 96), ("Precio", 86), ("Fecha", 128),
]
COLS_CLIENTES = [("Cédula", 180), ("Nombre", 250), ("Teléfono", 190)]


def moneda(valor: float) -> str:
  return f"${valor:,.2f}"


def texto_precio(valor: float) -> str:
  return str(int(valor)) if valor == int(valor) else f"{valor:.2f}"


class DialogoVenta(ctk.CTkToplevel):
  """Una sola ventana para elegir cliente, vehículo y precio de la venta."""

  def __init__(self, master, clientes, vehiculos):
    super().__init__(master)
    self.title("Registrar Venta")
    self.geometry("500x300")
    self.resizable(False, False)
    self.resultado = None

    self._clientes = {
        f"{c.get_cedula()} - {c.get_nombre()}": c for c in clientes
    }
    self._vehiculos = {
        f"{v.get_vin()} - {v.get_marca()} {v.get_modelo()}": v
        for v in vehiculos
    }

    ctk.CTkLabel(self, text="Cliente:").place(x=20, y=25)
    self.combo_cliente = ctk.CTkComboBox(
        self, values=list(self._clientes), width=340, state="readonly"
    )
    self.combo_cliente.place(x=130, y=25)
    self.combo_cliente.set("Selecciona un cliente...")

    ctk.CTkLabel(self, text="Vehículo:").place(x=20, y=70)
    self.combo_vehiculo = ctk.CTkComboBox(
        self,
        values=list(self._vehiculos),
        width=340,
        state="readonly",
        command=self._al_elegir_vehiculo,
    )
    self.combo_vehiculo.place(x=130, y=70)
    self.combo_vehiculo.set("Selecciona un vehículo...")

    self.lbl_base = ctk.CTkLabel(self, text="", text_color="gray")
    self.lbl_base.place(x=130, y=103)

    ctk.CTkLabel(self, text="Precio final:").place(x=20, y=140)
    self.entry_precio = ctk.CTkEntry(self, width=200)
    self.entry_precio.place(x=130, y=140)

    ctk.CTkButton(
        self, text="Confirmar venta", command=self._confirmar,
        fg_color="#f39c12", hover_color="#d35400", width=200,
    ).place(x=40, y=220)
    ctk.CTkButton(
        self, text="Cancelar", command=self.destroy,
        fg_color="#7f8c8d", hover_color="#626d6e", width=200,
    ).place(x=260, y=220)

    self.transient(master)
    self.after(150, self._activar_modal)

  def _activar_modal(self):
    try:
      self.grab_set()
      self.focus()
    except TclError:
      pass  # la ventana se cerró antes de activarse

  def _al_elegir_vehiculo(self, eleccion):
    vehiculo = self._vehiculos.get(eleccion)
    if vehiculo is None:
      return
    base = vehiculo.get_precio_base()
    self.lbl_base.configure(text=f"Precio base: {moneda(base)}")
    self.entry_precio.delete(0, "end")
    self.entry_precio.insert(0, texto_precio(base))

  def _confirmar(self):
    cliente = self._clientes.get(self.combo_cliente.get())
    vehiculo = self._vehiculos.get(self.combo_vehiculo.get())
    precio = self.entry_precio.get().strip()
    if cliente is None or vehiculo is None or not precio:
      messagebox.showwarning(
          "Datos incompletos",
          "Elige un cliente, un vehículo y escribe el precio final.",
          parent=self,
      )
      return
    self.resultado = (cliente.get_cedula(), vehiculo.get_vin(), precio)
    self.destroy()


class VistaApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("Sistema de Gestión: Venta y Almacén de Vehículos")
    self.geometry("1180x735")
    self.resizable(False, False)

    try:
      self.controlador = ControladorPrincipal()
    except (sqlite3.Error, OSError) as e:
      messagebox.showerror(
          "Base de datos",
          f"No se pudo abrir o crear la base de datos local:\n\n{e}",
      )
      self.destroy()
      raise SystemExit(1)

    self.modo = "inventario"
    self.widgets_detalle = {}
    self.etiquetas_detalle = []

    self.label_titulo = ctk.CTkLabel(
        self, text="Almacén y Venta de Vehículos", font=("Segoe UI", 22, "bold")
    )
    self.label_titulo.pack(pady=8)

    self._crear_panel_formulario()
    self._crear_panel_acciones()

    self.lbl_estado = ctk.CTkLabel(
        self, text="", anchor="w", font=("Arial", 10), text_color="gray",
        width=1140,
    )
    self.lbl_estado.place(x=20, y=700)

    self.construir_campos_detalle("Auto")
    self.ver_inventario()

  # ------------------------------------------------------ construcción UI
  def _crear_panel_formulario(self):
    self.frame_form = ctk.CTkFrame(self, width=420, height=625)
    self.frame_form.place(x=20, y=55)
    self.frame_form.pack_propagate(False)

    ctk.CTkLabel(
        self.frame_form, text="Registro de Vehículo", font=("Arial", 14, "bold")
    ).place(x=20, y=8)

    self.entry_vin = self.crear_campo(self.frame_form, "VIN:", 40)
    self.entry_marca = self.crear_campo(self.frame_form, "Marca:", 76)
    self.entry_modelo = self.crear_campo(self.frame_form, "Modelo:", 112)
    self.entry_anio = self.crear_campo(self.frame_form, "Año:", 148)
    self.entry_precio = self.crear_campo(self.frame_form, "Precio Base:", 184)

    ctk.CTkLabel(
        self.frame_form, text="Tipo Vehículo:", font=("Arial", 11)
    ).place(x=20, y=220)
    self.option_tipo = ctk.CTkOptionMenu(
        self.frame_form,
        values=list(CAMPOS_DETALLE),
        command=self.construir_campos_detalle,
        width=210,
        height=26,
    )
    self.option_tipo.place(x=170, y=220)

    self.btn_guardar = ctk.CTkButton(
        self.frame_form,
        text="Guardar Vehículo",
        command=self.guardar_vehiculo_interfaz,
        fg_color="#2ecc71",
        hover_color="#27ae60",
        width=360,
        height=32,
    )
    self.btn_guardar.place(x=30, y=368)

    ctk.CTkLabel(
        self.frame_form, text="Gestión de Clientes", font=("Arial", 14, "bold")
    ).place(x=20, y=412)

    self.entry_cedula = self.crear_campo(self.frame_form, "Cédula:", 444)
    self.entry_nom_cliente = self.crear_campo(self.frame_form, "Nombre:", 480)
    self.entry_tel_cliente = self.crear_campo(self.frame_form, "Teléfono:", 516)

    self.btn_guardar_cliente = ctk.CTkButton(
        self.frame_form,
        text="Registrar Cliente",
        command=self.registrar_cliente_interfaz,
        fg_color="#3498db",
        hover_color="#2980b9",
        width=170,
        height=32,
    )
    self.btn_guardar_cliente.place(x=30, y=565)

    self.btn_ver_clientes = ctk.CTkButton(
        self.frame_form,
        text="Ver Clientes",
        command=self.ver_clientes_interfaz,
        fg_color="#9b59b6",
        hover_color="#8e44ad",
        width=170,
        height=32,
    )
    self.btn_ver_clientes.place(x=220, y=565)

  def _crear_panel_acciones(self):
    self.frame_acciones = ctk.CTkFrame(self, width=700, height=625)
    self.frame_acciones.place(x=460, y=55)
    self.frame_acciones.pack_propagate(False)

    ctk.CTkLabel(
        self.frame_acciones,
        text="Gestión de Inventario y Memoria",
        font=("Arial", 15, "bold"),
    ).pack(pady=10)

    def boton(texto, comando, x, y, color=None, hover=None):
      b = ctk.CTkButton(
          self.frame_acciones, text=texto, command=comando, width=160,
          **({"fg_color": color, "hover_color": hover} if color else {}),
      )
      b.place(x=x, y=y)
      return b

    # Fila 1: consultas y venta
    self.btn_inventario = boton("Ver Inventario (Lista)", self.ver_inventario, 15, 45)
    self.btn_disponibles = boton("Ver Disponibles", self.ver_disponibles, 185, 45)
    self.btn_vendidos = boton("Historial Ventas (Pila)", self.ver_vendidos, 355, 45)
    self.btn_vender = boton(
        "Registrar Venta", self.registrar_venta_interfaz, 525, 45,
        "#f39c12", "#d35400",
    )
    # Fila 2: edición
    self.btn_precio = boton(
        "Actualizar Precio", self.actualizar_precio_interfaz, 15, 85
    )
    self.btn_eliminar = boton(
        "Eliminar por VIN", self.eliminar_vehiculo_interfaz, 185, 85,
        "#e74c3c", "#c0392b",
    )
    self.btn_anular = boton(
        "Anular Última Venta", self.anular_venta_interfaz, 355, 85,
        "#e67e22", "#ca6f1e",
    )
    self.btn_recibo = boton("Ver Recibo", self.ver_recibo_interfaz, 525, 85)

    # Tabla
    self.tree_frame = ctk.CTkFrame(self.frame_acciones, width=680, height=395)
    self.tree_frame.place(x=10, y=130)
    self.tree_frame.pack_propagate(False)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background="#2a2d2e",
        foreground="white",
        fieldbackground="#2a2d2e",
        rowheight=25,
    )
    style.configure(
        "Treeview.Heading",
        background="#1f538d",
        foreground="white",
        font=("Arial", 10, "bold"),
    )
    style.map("Treeview", background=[("selected", "#1f538d")])

    self.tree = ttk.Treeview(self.tree_frame, show="headings", selectmode="browse")
    barra = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
    self.tree.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y", pady=5)
    self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
    self.tree.tag_configure("vendido", foreground="#e67e22")
    self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar)

    # Barra de detalle + navegación por la lista doblemente enlazada
    self.lbl_detalle = ctk.CTkLabel(
        self.frame_acciones,
        text="Selecciona un registro para ver su detalle.",
        anchor="nw",
        justify="left",
        wraplength=670,
        width=680,
        height=44,
    )
    self.lbl_detalle.place(x=10, y=532)

    self.btn_anterior = ctk.CTkButton(
        self.frame_acciones, text="◀ Anterior", command=self.vehiculo_anterior,
        width=130,
    )
    self.btn_anterior.place(x=15, y=584)
    self.btn_siguiente = ctk.CTkButton(
        self.frame_acciones, text="Siguiente ▶", command=self.vehiculo_siguiente,
        width=130,
    )
    self.btn_siguiente.place(x=155, y=584)

  def crear_campo(self, parent, label_text, y_pos):
    lbl = ctk.CTkLabel(parent, text=label_text, font=("Arial", 11))
    lbl.place(x=20, y=y_pos)
    entry = ctk.CTkEntry(parent, width=210, height=26)
    entry.place(x=170, y=y_pos)
    return entry

  def construir_campos_detalle(self, tipo):
    """Muestra los 3 campos propios del tipo de vehículo elegido."""
    for widget in self.etiquetas_detalle + list(self.widgets_detalle.values()):
      widget.destroy()
    self.etiquetas_detalle = []
    self.widgets_detalle = {}

    for i, (clave, etiqueta, clase, opciones) in enumerate(CAMPOS_DETALLE[tipo]):
      y = 256 + i * 36
      lbl = ctk.CTkLabel(self.frame_form, text=etiqueta, font=("Arial", 11))
      lbl.place(x=20, y=y)
      if clase == "entry":
        widget = ctk.CTkEntry(
            self.frame_form, width=210, height=26, placeholder_text=opciones
        )
      else:
        widget = ctk.CTkOptionMenu(
            self.frame_form, values=opciones, width=210, height=26
        )
      widget.place(x=170, y=y)
      self.etiquetas_detalle.append(lbl)
      self.widgets_detalle[clave] = widget

  # ------------------------------------------------------------- tabla
  def mostrar_tabla(self, modo, columnas, filas):
    """filas: lista de (clave, valores, etiqueta_de_color o None)."""
    self.modo = modo
    for item in self.tree.get_children():
      self.tree.delete(item)

    ids = [f"c{i}" for i in range(len(columnas))]
    self.tree["columns"] = ids
    for cid, (titulo, ancho) in zip(ids, columnas):
      self.tree.heading(cid, text=titulo)
      self.tree.column(cid, width=ancho, anchor="w")

    for clave, valores, etiqueta in filas:
      self.tree.insert(
          "", "end", iid=clave, values=valores,
          tags=(etiqueta,) if etiqueta else (),
      )

    navegable = modo == "inventario"
    estado = "normal" if navegable else "disabled"
    self.btn_anterior.configure(state=estado)
    self.btn_siguiente.configure(state=estado)
    self.lbl_detalle.configure(
        text="Selecciona un registro para ver su detalle."
    )
    self.actualizar_estado()

  def actualizar_estado(self):
    total = len(self.controlador.inventario)
    vendidos = self.controlador.historial_ventas_pila.tamano()
    ultima = self.controlador.ultima_venta()
    ultima_txt = ultima.id_venta if ultima else "—"
    self.lbl_estado.configure(
        text=(
            f"Vehículos: {total}   |   Disponibles: {total - vendidos}   |"
            f"   Ventas: {vendidos}   |   Última venta: {ultima_txt}   |"
            f"   Base de datos: {self.controlador.db.ruta}"
        )
    )

  def al_seleccionar(self, _evento=None):
    seleccion = self.tree.selection()
    if not seleccion:
      return
    clave = seleccion[0]
    if self.modo == "inventario":
      vehiculo = self.controlador.inventario.ir_a(clave)
      if vehiculo:
        self.lbl_detalle.configure(
            text=(
                f"{vehiculo}\n"
                f"{vehiculo.get_marca()} {vehiculo.get_modelo()}"
                f" {vehiculo.get_anio()}  ·  {vehiculo.detalle()}  ·"
                f"  {moneda(vehiculo.get_precio_base())}"
            )
        )
    elif self.modo == "ventas":
      venta = self.controlador.obtener_venta(clave)
      if venta:
        self.lbl_detalle.configure(
            text=(
                f"Venta {venta.id_venta}  ·"
                f" {venta.fecha.strftime('%d/%m/%Y %H:%M')}\n"
                f"{venta.cliente.get_nombre()} ({venta.cliente.get_cedula()})"
                f"  →  {venta.vehiculo.get_marca()} {venta.vehiculo.get_modelo()}"
                f" [{venta.vehiculo.get_vin()}]  ·  {moneda(venta.precio_venta)}"
            )
        )
    elif self.modo == "clientes":
      for c in self.controlador.obtener_clientes():
        if c.get_cedula() == clave:
          self.lbl_detalle.configure(text=str(c))

  def _mover_cursor(self, vehiculo):
    if vehiculo is None:
      return
    self.tree.selection_set(vehiculo.get_vin())
    self.tree.see(vehiculo.get_vin())

  def vehiculo_siguiente(self):
    self._mover_cursor(self.controlador.inventario.siguiente())

  def vehiculo_anterior(self):
    self._mover_cursor(self.controlador.inventario.anterior())

  # ------------------------------------------------------------- vistas
  def ver_inventario(self):
    vehiculos = self.controlador.consultar_vehiculos()
    vendidos = self.controlador.vins_vendidos()
    filas = []
    for v in vehiculos:
      vendido = v.get_vin() in vendidos
      filas.append((
          v.get_vin(),
          (
              v.get_vin(), v.get_marca(), v.get_modelo(), v.get_anio(),
              v.TIPO, moneda(v.get_precio_base()),
              "Vendido" if vendido else "Disponible", v.detalle(),
          ),
          "vendido" if vendido else None,
      ))
    self.mostrar_tabla("inventario", COLS_INVENTARIO, filas)

  def ver_disponibles(self):
    filas = [
        (
            v.get_vin(),
            (
                v.get_vin(), v.get_marca(), v.get_modelo(), v.get_anio(),
                v.TIPO, moneda(v.get_precio_base()),
            ),
            None,
        )
        for v in self.controlador.obtener_vehiculos_disponibles()
    ]
    self.mostrar_tabla("disponibles", COLS_DISPONIBLES, filas)

  def ver_vendidos(self):
    filas = [
        (
            venta.id_venta,
            (
                venta.id_venta,
                venta.vehiculo.get_vin(),
                f"{venta.vehiculo.get_marca()} {venta.vehiculo.get_modelo()}",
                venta.cliente.get_nombre(),
                venta.cliente.get_telefono(),
                moneda(venta.precio_venta),
                venta.fecha.strftime("%d/%m/%Y %H:%M"),
            ),
            None,
        )
        for venta in self.controlador.historial_ventas()  # cima primero
    ]
    self.mostrar_tabla("ventas", COLS_VENTAS, filas)

  def ver_clientes_interfaz(self):
    filas = [
        (
            c.get_cedula(),
            (c.get_cedula(), c.get_nombre(), c.get_telefono()),
            None,
        )
        for c in self.controlador.obtener_clientes()
    ]
    self.mostrar_tabla("clientes", COLS_CLIENTES, filas)

  # ----------------------------------------------------------- acciones
  def recoger_detalles(self):
    return {clave: w.get().strip() for clave, w in self.widgets_detalle.items()}

  def guardar_vehiculo_interfaz(self):
    vin = self.entry_vin.get().strip()
    marca = self.entry_marca.get().strip()
    modelo = self.entry_modelo.get().strip()
    anio = self.entry_anio.get().strip()
    precio = self.entry_precio.get().strip()
    tipo = self.option_tipo.get()
    detalles = self.recoger_detalles()

    if not (vin and marca and modelo and anio and precio):
      messagebox.showwarning(
          "Campos Incompletos",
          "Por favor llena los datos generales del vehículo.",
      )
      return
    if any(valor == "" for valor in detalles.values()):
      messagebox.showwarning(
          "Campos Incompletos", f"Completa los datos propios del {tipo}."
      )
      return

    exito, mensaje = self.controlador.guardar_vehiculo(
        vin, marca, modelo, anio, precio, tipo, detalles
    )
    if exito:
      messagebox.showinfo("Éxito", mensaje)
      for entry in (
          self.entry_vin, self.entry_marca, self.entry_modelo,
          self.entry_anio, self.entry_precio,
      ):
        entry.delete(0, "end")
      self.construir_campos_detalle(tipo)
      self.ver_inventario()
    else:
      messagebox.showerror("Error", mensaje)

  def registrar_cliente_interfaz(self):
    cedula = self.entry_cedula.get().strip()
    nombre = self.entry_nom_cliente.get().strip()
    telefono = self.entry_tel_cliente.get().strip()

    if not cedula or not nombre or not telefono:
      messagebox.showwarning(
          "Campos Vacíos", "Por favor completa todos los datos del cliente."
      )
      return

    exito, mensaje = self.controlador.guardar_cliente(cedula, nombre, telefono)
    if exito:
      messagebox.showinfo("Éxito", mensaje)
      for entry in (
          self.entry_cedula, self.entry_nom_cliente, self.entry_tel_cliente
      ):
        entry.delete(0, "end")
      self.ver_clientes_interfaz()
    else:
      messagebox.showerror("Error", mensaje)

  def registrar_venta_interfaz(self):
    clientes = self.controlador.obtener_clientes()
    disponibles = self.controlador.obtener_vehiculos_disponibles()
    if not clientes:
      messagebox.showwarning(
          "Sin clientes", "Primero registra al menos un cliente."
      )
      return
    if not disponibles:
      messagebox.showwarning(
          "Sin vehículos", "No hay vehículos disponibles para vender."
      )
      return

    dialogo = DialogoVenta(self, clientes, disponibles)
    self.wait_window(dialogo)
    if dialogo.resultado is None:
      return

    cedula, vin, precio = dialogo.resultado
    exito, mensaje = self.controlador.registrar_venta(cedula, vin, precio)
    if exito:
      recibo = self.controlador.ultima_venta().generar_recibo()
      messagebox.showinfo("¡Venta Exitosa!", f"{mensaje}\n\n{recibo}")
      self.ver_vendidos()
    else:
      messagebox.showerror("Error", mensaje)

  def _vin_objetivo(self, titulo, texto):
    """VIN de la fila seleccionada o, si no hay, el que escriba el usuario."""
    if self.modo in ("inventario", "disponibles"):
      seleccion = self.tree.selection()
      if seleccion:
        return seleccion[0]
    return ctk.CTkInputDialog(text=texto, title=titulo).get_input()

  def eliminar_vehiculo_interfaz(self):
    vin = self._vin_objetivo(
        "Eliminar Vehículo", "Ingresa el VIN del vehículo a eliminar:"
    )
    if not vin:
      return
    if not messagebox.askyesno(
        "Confirmar", f"¿Seguro que quieres eliminar el vehículo {vin.upper()}?"
    ):
      return
    exito, mensaje = self.controlador.eliminar_vehiculo(vin)
    if exito:
      messagebox.showinfo("Éxito", mensaje)
      self.ver_inventario()
    else:
      messagebox.showerror("Error", mensaje)

  def actualizar_precio_interfaz(self):
    vin = self._vin_objetivo(
        "Actualizar Precio", "Ingresa el VIN del vehículo:"
    )
    if not vin:
      return
    nuevo = ctk.CTkInputDialog(
        text=f"Nuevo precio base para {vin.upper()}:", title="Actualizar Precio"
    ).get_input()
    if not nuevo:
      return
    exito, mensaje = self.controlador.actualizar_precio_vehiculo(vin, nuevo)
    if exito:
      messagebox.showinfo("Éxito", mensaje)
      self.ver_inventario()
    else:
      messagebox.showerror("Error", mensaje)

  def anular_venta_interfaz(self):
    venta = self.controlador.ultima_venta()
    if venta is None:
      messagebox.showinfo("Sin ventas", "Aún no hay ventas registradas.")
      return
    if not messagebox.askyesno(
        "Anular última venta",
        f"¿Anular la venta {venta.id_venta}"
        f" ({venta.vehiculo.get_vin()} → {venta.cliente.get_nombre()})?\n\n"
        "El vehículo volverá a estar disponible.",
    ):
      return
    exito, mensaje = self.controlador.anular_ultima_venta()
    if exito:
      messagebox.showinfo("Éxito", mensaje)
      self.ver_vendidos()
    else:
      messagebox.showerror("Error", mensaje)

  def ver_recibo_interfaz(self):
    venta = None
    if self.modo == "ventas" and self.tree.selection():
      venta = self.controlador.obtener_venta(self.tree.selection()[0])
    if venta is None:
      venta = self.controlador.ultima_venta()
    if venta is None:
      messagebox.showinfo("Sin ventas", "Aún no hay ventas registradas.")
      return
    messagebox.showinfo(f"Recibo {venta.id_venta}", venta.generar_recibo())


if __name__ == "__main__":
  app = VistaApp()
  app.mainloop()
