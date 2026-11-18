from modelo.vehiculo import Vehiculo


class Moto(Vehiculo):

  TIPO = "Moto"
  TABLA_DETALLE = "detalles_moto"

  def __init__(
      self,
      vin: str,
      marca: str,
      modelo: str,
      anio: int,
      precio_base: float,
      cilindraje: int,
      tipo_manubrio: str,
      tiene_abs: bool,
  ):
    super().__init__(vin, marca, modelo, anio, precio_base)
    self.set_cilindraje(cilindraje)
    self.set_tipo_manubrio(tipo_manubrio)
    self.set_tiene_abs(tiene_abs)

  def get_cilindraje(self) -> int:
    return self.cilindraje

  def set_cilindraje(self, cilindraje: int):
    if isinstance(cilindraje, bool) or not isinstance(cilindraje, int):
      raise ValueError("El cilindraje debe ser un número entero.")
    if not 50 <= cilindraje <= 3000:
      raise ValueError("El cilindraje debe estar entre 50 y 3000 cc.")
    self.cilindraje = cilindraje

  def get_tipo_manubrio(self) -> str:
    return self.tipo_manubrio

  def set_tipo_manubrio(self, tipo_manubrio: str):
    tipo_manubrio = (tipo_manubrio or "").strip()
    if not tipo_manubrio:
      raise ValueError("El tipo de manubrio no puede estar vacío.")
    self.tipo_manubrio = tipo_manubrio

  def is_tiene_abs(self) -> bool:
    return self.tiene_abs

  def set_tiene_abs(self, tiene_abs: bool):
    self.tiene_abs = bool(tiene_abs)

  def detalle(self) -> str:
    abs_txt = "con ABS" if self.tiene_abs else "sin ABS"
    return f"{self.cilindraje}cc, manubrio {self.tipo_manubrio}, {abs_txt}"

  def datos_detalle(self) -> dict:
    return {
        "cilindraje": self.cilindraje,
        "tipo_manubrio": self.tipo_manubrio,
        "tiene_abs": int(self.tiene_abs),
    }

  def __str__(self) -> str:
    return (
        f"Moto [VIN={self.vin}, Marca={self.marca},"
        f" Cilindraje={self.cilindraje}cc]"
    )
