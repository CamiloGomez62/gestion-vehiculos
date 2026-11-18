import math

from modelo.vehiculo import Vehiculo


class Camion(Vehiculo):

  TIPO = "Camión"
  TABLA_DETALLE = "detalles_camion"

  def __init__(
      self,
      vin: str,
      marca: str,
      modelo: str,
      anio: int,
      precio_base: float,
      capacidad_carga: float,
      num_ejes: int,
      tipo_carroceria: str,
  ):
    super().__init__(vin, marca, modelo, anio, precio_base)
    self.set_capacidad_carga(capacidad_carga)
    self.set_num_ejes(num_ejes)
    self.set_tipo_carroceria(tipo_carroceria)

  def get_capacidad_carga(self) -> float:
    return self.capacidad_carga

  def set_capacidad_carga(self, capacidad_carga: float):
    try:
      capacidad_carga = float(capacidad_carga)
    except (TypeError, ValueError):
      raise ValueError("La capacidad de carga debe ser un número.")
    if not math.isfinite(capacidad_carga) or capacidad_carga <= 0:
      raise ValueError("La capacidad de carga debe ser mayor a cero.")
    self.capacidad_carga = capacidad_carga

  def get_num_ejes(self) -> int:
    return self.num_ejes

  def set_num_ejes(self, num_ejes: int):
    if isinstance(num_ejes, bool) or not isinstance(num_ejes, int):
      raise ValueError("El número de ejes debe ser un entero.")
    if not 2 <= num_ejes <= 10:
      raise ValueError("El número de ejes debe estar entre 2 y 10.")
    self.num_ejes = num_ejes

  def get_tipo_carroceria(self) -> str:
    return self.tipo_carroceria

  def set_tipo_carroceria(self, tipo_carroceria: str):
    tipo_carroceria = (tipo_carroceria or "").strip()
    if not tipo_carroceria:
      raise ValueError("El tipo de carrocería no puede estar vacío.")
    self.tipo_carroceria = tipo_carroceria

  def detalle(self) -> str:
    return (
        f"{self.capacidad_carga:g} ton, {self.num_ejes} ejes,"
        f" {self.tipo_carroceria}"
    )

  def datos_detalle(self) -> dict:
    return {
        "capacidad_carga": self.capacidad_carga,
        "num_ejes": self.num_ejes,
        "tipo_carroceria": self.tipo_carroceria,
    }

  def __str__(self) -> str:
    return (
        f"Camión [VIN={self.vin}, Carga={self.capacidad_carga:g}T,"
        f" Ejes={self.num_ejes}]"
    )
