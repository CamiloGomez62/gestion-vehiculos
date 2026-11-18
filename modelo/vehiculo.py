import math
import re
from abc import ABC, abstractmethod
from datetime import date


class Vehiculo(ABC):
  """Clase base abstracta de todos los vehículos del concesionario.

  Los setters validan el dato y lanzan ValueError si no es válido, así que
  cualquier vehículo creado (o editado) por el programa es consistente.
  """

  TIPO = ""
  TABLA_DETALLE = ""

  def __init__(
      self, vin: str, marca: str, modelo: str, anio: int, precio_base: float
  ):
    self.set_vin(vin)
    self.set_marca(marca)
    self.set_modelo(modelo)
    self.set_anio(anio)
    self.set_precio_base(precio_base)

  # ------------------------------------------------------------ getters
  def get_vin(self) -> str:
    return self.vin

  def get_marca(self) -> str:
    return self.marca

  def get_modelo(self) -> str:
    return self.modelo

  def get_anio(self) -> int:
    return self.anio

  def get_precio_base(self) -> float:
    return self.precio_base

  # ------------------------------------------------------------ setters
  def set_vin(self, vin: str):
    vin = (vin or "").strip().upper()
    if not vin:
      raise ValueError("El VIN no puede estar vacío.")
    if len(vin) > 20:
      raise ValueError("El VIN no puede tener más de 20 caracteres.")
    if not re.fullmatch(r"[A-Z0-9\-]+", vin):
      raise ValueError("El VIN solo puede tener letras, números y guiones.")
    self.vin = vin

  def set_marca(self, marca: str):
    marca = (marca or "").strip()
    if not marca:
      raise ValueError("La marca no puede estar vacía.")
    self.marca = marca

  def set_modelo(self, modelo: str):
    modelo = (modelo or "").strip()
    if not modelo:
      raise ValueError("El modelo no puede estar vacío.")
    self.modelo = modelo

  def set_anio(self, anio: int):
    limite = date.today().year + 1
    if isinstance(anio, bool) or not isinstance(anio, int):
      raise ValueError("El año debe ser un número entero.")
    if not 1900 <= anio <= limite:
      raise ValueError(f"El año debe estar entre 1900 y {limite}.")
    self.anio = anio

  def set_precio_base(self, precio_base: float):
    try:
      precio_base = float(precio_base)
    except (TypeError, ValueError):
      raise ValueError("El precio debe ser un número.")
    if not math.isfinite(precio_base) or precio_base <= 0:
      raise ValueError("El precio base debe ser mayor a cero.")
    self.precio_base = precio_base

  # ------------------------------------------------- métodos abstractos
  @abstractmethod
  def detalle(self) -> str:
    """Texto corto con las características propias del tipo de vehículo."""

  @abstractmethod
  def datos_detalle(self) -> dict:
    """Columnas -> valores de la tabla de detalle de este tipo."""
