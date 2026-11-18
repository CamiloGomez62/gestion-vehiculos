import functools
import logging
import re
import sqlite3
from datetime import datetime

from controlador.conexion import Conexion
from modelo.automovil import Automovil
from modelo.camion import Camion
from modelo.cliente import Cliente
from modelo.estructuras import PilaVentas
from modelo.inventario import Inventario
from modelo.moto import Moto
from modelo.venta import FORMATO_FECHA, Venta

TIPOS_VEHICULO = ("Auto", "Moto", "Camión")

_SELECT_VEHICULOS = """
    SELECT v.vin, v.marca, v.modelo, v.anio, v.precio_base, v.tipo_vehiculo,
           a.num_puertas, a.tipo_combustible, a.tiene_camara,
           m.cilindraje, m.tipo_manubrio, m.tiene_abs,
           c.capacidad_carga, c.num_ejes, c.tipo_carroceria
    FROM vehiculos v
    LEFT JOIN detalles_auto a ON a.vin = v.vin
    LEFT JOIN detalles_moto m ON m.vin = v.vin
    LEFT JOIN detalles_camion c ON c.vin = v.vin
"""


# ---------------------------------------------------------------- utilidades
def _a_entero(texto, campo: str) -> int:
  try:
    return int(str(texto).strip())
  except ValueError:
    raise ValueError(f"{campo} debe ser un número entero.")


def _a_decimal(valor, campo: str) -> float:
  """Convierte texto a número aceptando formatos como 35000, 35.000.000,
  35,000.50 o 35,50 (separador decimal con coma)."""
  if not isinstance(valor, str):
    return float(valor)
  limpio = valor.strip().replace("$", "").replace(" ", "")
  if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", limpio):
    limpio = limpio.replace(".", "").replace(",", ".")
  elif re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", limpio):
    limpio = limpio.replace(",", "")
  elif re.fullmatch(r"\d+,\d{1,2}", limpio):
    limpio = limpio.replace(",", ".")
  if not re.fullmatch(r"\d+(\.\d+)?", limpio):
    raise ValueError(f"{campo} debe ser un número (ej. 35000 o 35000.50).")
  return float(limpio)


def _a_booleano(texto) -> bool:
  return str(texto).strip().lower() in ("sí", "si", "s", "true", "1", "yes")


def _mensaje_integridad(error: sqlite3.IntegrityError) -> str:
  texto = str(error)
  if "UNIQUE" in texto or "PRIMARY KEY" in texto:
    if "vehiculos.vin" in texto:
      return "Ya existe un vehículo con ese VIN."
    if "clientes.cedula" in texto:
      return "Ya existe un cliente con esa cédula."
    if "ventas.vin_vehiculo" in texto:
      return "Ese vehículo ya fue vendido."
    if "ventas.id_venta" in texto:
      return "Ya existe una venta con ese ID."
  if "FOREIGN KEY" in texto:
    return (
        "La operación no es posible porque hay datos relacionados (por"
        " ejemplo, un vehículo con una venta registrada)."
    )
  if "CHECK" in texto:
    return "Alguno de los valores no cumple las reglas de la base de datos."
  return f"Error de integridad en la base de datos: {texto}"


def _seguro(funcion):
  """Las operaciones que modifican datos devuelven siempre (éxito, mensaje)."""

  @functools.wraps(funcion)
  def envoltura(self, *args, **kwargs):
    try:
      return funcion(self, *args, **kwargs)
    except ValueError as e:
      return False, str(e)
    except sqlite3.IntegrityError as e:
      return False, _mensaje_integridad(e)
    except sqlite3.Error as e:
      return False, f"Error de base de datos: {e}"

  return envoltura


def _lectura(funcion):
  """Las consultas devuelven una lista vacía si algo falla."""

  @functools.wraps(funcion)
  def envoltura(self, *args, **kwargs):
    try:
      return funcion(self, *args, **kwargs)
    except sqlite3.Error:
      logging.exception("Error al consultar la base de datos")
      return []

  return envoltura


class ControladorPrincipal:

  def __init__(self, db: Conexion = None):
    self.db = db or Conexion()
    self.inventario = Inventario()
    self.historial_ventas_pila = PilaVentas()
    self.cargar_historial_ventas()

  # ------------------------------------------------------- construcción
  @staticmethod
  def _crear_vehiculo(tipo, vin, marca, modelo, anio, precio, d):
    """Crea el objeto del modelo a partir de los textos del formulario.

    Los constructores validan todos los datos (lanzan ValueError).
    """
    anio = _a_entero(anio, "El año")
    precio = _a_decimal(precio, "El precio")
    if tipo == "Auto":
      return Automovil(
          vin, marca, modelo, anio, precio,
          _a_entero(d.get("puertas", ""), "Las puertas"),
          d.get("combustible", ""),
          _a_booleano(d.get("camara", "No")),
      )
    if tipo == "Moto":
      return Moto(
          vin, marca, modelo, anio, precio,
          _a_entero(d.get("cilindraje", ""), "El cilindraje"),
          d.get("manubrio", ""),
          _a_booleano(d.get("abs", "No")),
      )
    if tipo == "Camión":
      return Camion(
          vin, marca, modelo, anio, precio,
          _a_decimal(d.get("carga", ""), "La capacidad de carga"),
          _a_entero(d.get("ejes", ""), "El número de ejes"),
          d.get("carroceria", ""),
      )
    raise ValueError("Tipo de vehículo no válido.")

  @staticmethod
  def _vehiculo_desde_fila(fila):
    tipo = fila["tipo_vehiculo"]
    base = (
        fila["vin"], fila["marca"], fila["modelo"], fila["anio"],
        fila["precio_base"],
    )
    if tipo == "Auto":
      return Automovil(
          *base, fila["num_puertas"], fila["tipo_combustible"],
          bool(fila["tiene_camara"]),
      )
    if tipo == "Moto":
      return Moto(
          *base, fila["cilindraje"], fila["tipo_manubrio"],
          bool(fila["tiene_abs"]),
      )
    if tipo == "Camión":
      return Camion(
          *base, fila["capacidad_carga"], fila["num_ejes"],
          fila["tipo_carroceria"],
      )
    raise ValueError(f"Tipo de vehículo desconocido: {tipo}")

  def _leer_vehiculos(self, conn, where: str = "", params=()):
    filas = conn.execute(
        f"{_SELECT_VEHICULOS} {where} ORDER BY v.rowid", params
    ).fetchall()
    vehiculos = []
    for fila in filas:
      try:
        vehiculos.append(self._vehiculo_desde_fila(fila))
      except (ValueError, TypeError) as e:
        logging.warning("Vehículo %s omitido (datos inválidos): %s", fila["vin"], e)
    return vehiculos

  @staticmethod
  def _leer_clientes(conn):
    clientes = []
    for fila in conn.execute(
        "SELECT cedula, nombre, telefono FROM clientes ORDER BY rowid"
    ):
      try:
        clientes.append(Cliente(fila["cedula"], fila["nombre"], fila["telefono"]))
      except ValueError as e:
        logging.warning("Cliente %s omitido (datos inválidos): %s", fila["cedula"], e)
    return clientes

  # ---------------------------------------------------------- vehículos
  @_seguro
  def guardar_vehiculo(
      self,
      vin: str,
      marca: str,
      modelo: str,
      anio: str,
      precio: str,
      tipo: str,
      detalles: dict,
  ):
    vehiculo = self._crear_vehiculo(tipo, vin, marca, modelo, anio, precio, detalles)
    with self.db.transaccion() as conn:
      conn.execute(
          "INSERT INTO vehiculos (vin, marca, modelo, anio, precio_base,"
          " tipo_vehiculo) VALUES (?, ?, ?, ?, ?, ?)",
          (
              vehiculo.get_vin(), vehiculo.get_marca(), vehiculo.get_modelo(),
              vehiculo.get_anio(), vehiculo.get_precio_base(), vehiculo.TIPO,
          ),
      )
      datos = {"vin": vehiculo.get_vin(), **vehiculo.datos_detalle()}
      columnas = ", ".join(datos)
      marcas = ", ".join("?" for _ in datos)
      conn.execute(
          f"INSERT INTO {vehiculo.TABLA_DETALLE} ({columnas}) VALUES ({marcas})",
          tuple(datos.values()),
      )
    return True, f"{tipo} guardado con éxito."

  @_lectura
  def consultar_vehiculos(self):
    """Lee todos los vehículos y refresca el inventario en memoria."""
    with self.db.transaccion() as conn:
      vehiculos = self._leer_vehiculos(conn)
    self.inventario.cargar(vehiculos)
    return vehiculos

  @_lectura
  def obtener_vehiculos_disponibles(self):
    with self.db.transaccion() as conn:
      return self._leer_vehiculos(
          conn, "WHERE v.vin NOT IN (SELECT vin_vehiculo FROM ventas)"
      )

  @_seguro
  def eliminar_vehiculo(self, vin: str):
    vin = (vin or "").strip().upper()
    if not vin:
      return False, "Escribe el VIN para eliminar."
    with self.db.transaccion() as conn:
      if conn.execute(
          "SELECT 1 FROM ventas WHERE vin_vehiculo = ?", (vin,)
      ).fetchone():
        return False, (
            "No se puede eliminar: ese vehículo tiene una venta registrada y"
            " debe conservarse en el historial."
        )
      cursor = conn.execute("DELETE FROM vehiculos WHERE vin = ?", (vin,))
      if cursor.rowcount == 0:
        return False, "No se encontró un vehículo con ese VIN."
    self.inventario.eliminar(vin)
    return True, "Vehículo eliminado."

  @_seguro
  def actualizar_precio_vehiculo(self, vin: str, nuevo_precio):
    vin = (vin or "").strip().upper()
    precio = _a_decimal(nuevo_precio, "El precio")
    with self.db.transaccion() as conn:
      vehiculos = self._leer_vehiculos(conn, "WHERE v.vin = ?", (vin,))
      if not vehiculos:
        return False, "No se encontró un vehículo con ese VIN."
      if conn.execute(
          "SELECT 1 FROM ventas WHERE vin_vehiculo = ?", (vin,)
      ).fetchone():
        return False, "No se puede cambiar el precio de un vehículo ya vendido."
      vehiculo = vehiculos[0]
      vehiculo.set_precio_base(precio)  # valida (> 0)
      conn.execute(
          "UPDATE vehiculos SET precio_base = ? WHERE vin = ?",
          (vehiculo.get_precio_base(), vin),
      )
    return True, f"Precio de {vin} actualizado a ${vehiculo.get_precio_base():,.2f}."

  # ----------------------------------------------------------- clientes
  @_seguro
  def guardar_cliente(self, cedula: str, nombre: str, telefono: str):
    cliente = Cliente(cedula, nombre, telefono)
    with self.db.transaccion() as conn:
      conn.execute(
          "INSERT INTO clientes (cedula, nombre, telefono) VALUES (?, ?, ?)",
          (cliente.get_cedula(), cliente.get_nombre(), cliente.get_telefono()),
      )
    return True, "Cliente registrado con éxito."

  @_lectura
  def obtener_clientes(self):
    with self.db.transaccion() as conn:
      return self._leer_clientes(conn)

  # ------------------------------------------------------------- ventas
  @staticmethod
  def _siguiente_id_venta(conn) -> str:
    mayor = 0
    for (id_venta,) in conn.execute("SELECT id_venta FROM ventas"):
      coincidencia = re.fullmatch(r"V-(\d+)", id_venta)
      if coincidencia:
        mayor = max(mayor, int(coincidencia.group(1)))
    return f"V-{mayor + 1:04d}"

  @_seguro
  def registrar_venta(
      self, cedula_cliente: str, vin_vehiculo: str, precio_venta, id_venta: str = None
  ):
    precio = _a_decimal(precio_venta, "El precio de venta")
    cedula = (cedula_cliente or "").strip()
    vin = (vin_vehiculo or "").strip().upper()

    with self.db.transaccion() as conn:
      clientes = [c for c in self._leer_clientes(conn) if c.get_cedula() == cedula]
      if not clientes:
        return False, "No existe un cliente con esa cédula. Regístralo primero."
      vehiculos = self._leer_vehiculos(conn, "WHERE v.vin = ?", (vin,))
      if not vehiculos:
        return False, "No existe un vehículo con ese VIN."
      if conn.execute(
          "SELECT 1 FROM ventas WHERE vin_vehiculo = ?", (vin,)
      ).fetchone():
        return False, "Ese vehículo ya fue vendido."

      id_venta = (id_venta or "").strip() or self._siguiente_id_venta(conn)
      venta = Venta(id_venta, clientes[0], vehiculos[0], precio)
      conn.execute(
          "INSERT INTO ventas (id_venta, cedula_cliente, vin_vehiculo,"
          " precio_venta, fecha) VALUES (?, ?, ?, ?, ?)",
          (
              venta.id_venta, cedula, vin, venta.precio_venta,
              venta.fecha.strftime(FORMATO_FECHA),
          ),
      )

    # Solo se apila cuando la base de datos ya confirmó la venta.
    self.historial_ventas_pila.apilar_venta(venta)
    return True, f"¡Venta {venta.id_venta} registrada con éxito!"

  @_seguro
  def anular_ultima_venta(self):
    """Deshace la venta de la cima de la pila (la más reciente)."""
    venta = self.historial_ventas_pila.obtener_ultima_venta()
    if venta is None:
      return False, "No hay ventas para anular."
    with self.db.transaccion() as conn:
      conn.execute("DELETE FROM ventas WHERE id_venta = ?", (venta.id_venta,))
    self.historial_ventas_pila.desapilar_venta()
    return True, (
        f"Venta {venta.id_venta} anulada. El vehículo"
        f" {venta.vehiculo.get_vin()} vuelve a estar disponible."
    )

  def cargar_historial_ventas(self) -> int:
    """Reconstruye la pila desde la BD (así sobrevive al cerrar el programa)."""
    pila = PilaVentas()
    try:
      with self.db.transaccion() as conn:
        vehiculos = {v.get_vin(): v for v in self._leer_vehiculos(conn)}
        clientes = {c.get_cedula(): c for c in self._leer_clientes(conn)}
        filas = conn.execute(
            "SELECT id_venta, cedula_cliente, vin_vehiculo, precio_venta, fecha"
            " FROM ventas ORDER BY rowid"
        ).fetchall()
      for fila in filas:
        cliente = clientes.get(fila["cedula_cliente"])
        vehiculo = vehiculos.get(fila["vin_vehiculo"])
        if cliente is None or vehiculo is None:
          logging.warning("Venta %s omitida: faltan datos.", fila["id_venta"])
          continue
        try:
          fecha = datetime.strptime(fila["fecha"], FORMATO_FECHA)
          pila.apilar_venta(
              Venta(fila["id_venta"], cliente, vehiculo, fila["precio_venta"], fecha)
          )
        except ValueError as e:
          logging.warning("Venta %s omitida: %s", fila["id_venta"], e)
    except sqlite3.Error:
      logging.exception("No se pudo cargar el historial de ventas")
    self.historial_ventas_pila = pila
    return pila.tamano()

  def historial_ventas(self):
    """Ventas de la más reciente a la más antigua (leyendo la pila)."""
    return self.historial_ventas_pila.listar_desde_cima()

  def ultima_venta(self):
    return self.historial_ventas_pila.obtener_ultima_venta()

  def obtener_venta(self, id_venta: str):
    for venta in self.historial_ventas_pila.elementos:
      if venta.id_venta == id_venta:
        return venta
    return None

  def vins_vendidos(self) -> set:
    return {v.vehiculo.get_vin() for v in self.historial_ventas_pila.elementos}
