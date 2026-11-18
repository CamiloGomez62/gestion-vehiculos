import re


class Cliente:

  def __init__(self, cedula: str, nombre: str, telefono: str):
    self.set_cedula(cedula)
    self.set_nombre(nombre)
    self.set_telefono(telefono)

  def get_cedula(self) -> str:
    return self.cedula

  def set_cedula(self, cedula: str):
    cedula = (cedula or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9\-]{3,20}", cedula):
      raise ValueError(
          "La cédula debe tener entre 3 y 20 letras o números (sin espacios)."
      )
    self.cedula = cedula

  def get_nombre(self) -> str:
    return self.nombre

  def set_nombre(self, nombre: str):
    nombre = " ".join((nombre or "").split())
    if not nombre:
      raise ValueError("El nombre no puede estar vacío.")
    if len(nombre) > 100:
      raise ValueError("El nombre no puede tener más de 100 caracteres.")
    self.nombre = nombre

  def get_telefono(self) -> str:
    return self.telefono

  def set_telefono(self, telefono: str):
    telefono = (telefono or "").strip()
    if not re.fullmatch(r"[0-9+\-\s()]{3,20}", telefono):
      raise ValueError(
          "El teléfono solo puede tener números, espacios, + - ( ) (3 a 20"
          " caracteres)."
      )
    self.telefono = telefono

  def __str__(self) -> str:
    return (
        f"Cliente [Cédula={self.cedula}, Nombre={self.nombre},"
        f" Teléfono={self.telefono}]"
    )
