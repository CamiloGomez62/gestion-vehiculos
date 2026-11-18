from modelo.estructuras import ListaDoblementeEnlazadaVehiculos
from modelo.vehiculo import Vehiculo


class Inventario:
  """Inventario en memoria, respaldado por una lista doblemente enlazada."""

  def __init__(self):
    self.lista_vehiculos = ListaDoblementeEnlazadaVehiculos()

  def agregar(self, v: Vehiculo):
    self.lista_vehiculos.agregar_vehiculo(v)

  def cargar(self, vehiculos):
    """Reemplaza el contenido del inventario (se usa al leer de la BD)."""
    self.lista_vehiculos.limpiar()
    for v in vehiculos:
      self.lista_vehiculos.agregar_vehiculo(v)

  def eliminar(self, vin: str) -> bool:
    return self.lista_vehiculos.eliminar_por_vin(vin)

  def buscar_por_vin(self, vin: str):
    return self.lista_vehiculos.buscar_vehiculo(vin)

  def get_lista_vehiculos(self) -> list:
    return self.lista_vehiculos.obtener_lista_python()

  def valor_total(self) -> float:
    return sum(v.get_precio_base() for v in self.lista_vehiculos)

  # Navegación con el cursor de la lista doblemente enlazada
  def ir_a(self, vin: str):
    return self.lista_vehiculos.ir_a(vin)

  def siguiente(self):
    return self.lista_vehiculos.avanzar()

  def anterior(self):
    return self.lista_vehiculos.retroceder()

  def __len__(self):
    return len(self.lista_vehiculos)
