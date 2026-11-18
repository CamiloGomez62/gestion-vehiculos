from modelo.vehiculo import Vehiculo


class Automovil(Vehiculo):

  TIPO = "Auto"
  TABLA_DETALLE = "detalles_auto"

  def __init__(
      self,
      vin: str,
      marca: str,
      modelo: str,
      anio: int,
      precio_base: float,
      num_puertas: int,
      tipo_combustible: str,
      tiene_camara_reversa: bool,
  ):
    super().__init__(vin, marca, modelo, anio, precio_base)
    self.set_num_puertas(num_puertas)
    self.set_tipo_combustible(tipo_combustible)
    self.set_tiene_camara_reversa(tiene_camara_reversa)

  def get_num_puertas(self) -> int:
    return self.num_puertas

  def set_num_puertas(self, num_puertas: int):
    if isinstance(num_puertas, bool) or not isinstance(num_puertas, int):
      raise ValueError("El número de puertas debe ser un entero.")
    if not 2 <= num_puertas <= 6:
      raise ValueError("El número de puertas debe estar entre 2 y 6.")
    self.num_puertas = num_puertas

  def get_tipo_combustible(self) -> str:
    return self.tipo_combustible

  def set_tipo_combustible(self, tipo_combustible: str):
    tipo_combustible = (tipo_combustible or "").strip()
    if not tipo_combustible:
      raise ValueError("El tipo de combustible no puede estar vacío.")
    self.tipo_combustible = tipo_combustible

  def is_tiene_camara_reversa(self) -> bool:
    return self.tiene_camara_reversa

  def set_tiene_camara_reversa(self, tiene_camara_reversa: bool):
    self.tiene_camara_reversa = bool(tiene_camara_reversa)

  def detalle(self) -> str:
    camara = "con cámara" if self.tiene_camara_reversa else "sin cámara"
    return f"{self.num_puertas} puertas, {self.tipo_combustible}, {camara}"

  def datos_detalle(self) -> dict:
    return {
        "num_puertas": self.num_puertas,
        "tipo_combustible": self.tipo_combustible,
        "tiene_camara": int(self.tiene_camara_reversa),
    }

  def __str__(self) -> str:
    return (
        f"Automovil[VIN={self.vin}, Modelo={self.modelo},"
        f" Puertas={self.num_puertas}]"
    )
