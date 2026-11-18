class NodoVehiculo:

  def __init__(self, vehiculo):
    self.vehiculo = vehiculo
    self.siguiente = None
    self.anterior = None


class ListaDoblementeEnlazadaVehiculos:
  """Lista doblemente enlazada de vehículos con un cursor (`actual`).

  Gracias a los enlaces `siguiente` y `anterior` se puede navegar el
  inventario hacia adelante y hacia atrás desde la interfaz.
  """

  def __init__(self):
    self.cabeza = None
    self.cola = None
    self.actual = None
    self._tamano = 0

  def agregar_vehiculo(self, vehiculo):
    nuevo_nodo = NodoVehiculo(vehiculo)
    if not self.cabeza:
      self.cabeza = nuevo_nodo
      self.cola = nuevo_nodo
    else:
      self.cola.siguiente = nuevo_nodo
      nuevo_nodo.anterior = self.cola
      self.cola = nuevo_nodo
    self._tamano += 1

  def buscar_nodo(self, vin: str):
    vin = (vin or "").strip().upper()
    nodo = self.cabeza
    while nodo:
      if nodo.vehiculo.vin == vin:
        return nodo
      nodo = nodo.siguiente
    return None

  def buscar_vehiculo(self, vin: str):
    nodo = self.buscar_nodo(vin)
    return nodo.vehiculo if nodo else None

  def eliminar_por_vin(self, vin: str) -> bool:
    nodo = self.buscar_nodo(vin)
    if nodo is None:
      return False

    if nodo.anterior:
      nodo.anterior.siguiente = nodo.siguiente
    else:
      self.cabeza = nodo.siguiente
    if nodo.siguiente:
      nodo.siguiente.anterior = nodo.anterior
    else:
      self.cola = nodo.anterior

    if self.actual is nodo:
      self.actual = nodo.siguiente or nodo.anterior
    self._tamano -= 1
    return True

  # ------------------------------------------------------------- cursor
  def ir_a(self, vin: str):
    """Coloca el cursor en el vehículo con ese VIN y lo devuelve."""
    nodo = self.buscar_nodo(vin)
    self.actual = nodo
    return nodo.vehiculo if nodo else None

  def avanzar(self):
    """Mueve el cursor al siguiente vehículo (o al primero si no hay)."""
    if not self.cabeza:
      return None
    if self.actual is None:
      self.actual = self.cabeza
    elif self.actual.siguiente:
      self.actual = self.actual.siguiente
    return self.actual.vehiculo

  def retroceder(self):
    """Mueve el cursor al vehículo anterior (o al último si no hay)."""
    if not self.cabeza:
      return None
    if self.actual is None:
      self.actual = self.cola
    elif self.actual.anterior:
      self.actual = self.actual.anterior
    return self.actual.vehiculo

  # ---------------------------------------------------------- utilidades
  def obtener_lista_python(self):
    """Devuelve los elementos en una lista normal para recorrerlos"""
    elementos = []
    actual = self.cabeza
    while actual:
      elementos.append(actual.vehiculo)
      actual = actual.siguiente
    return elementos

  def limpiar(self):
    self.cabeza = None
    self.cola = None
    self.actual = None
    self._tamano = 0

  def esta_vacia(self) -> bool:
    return self.cabeza is None

  def __len__(self):
    return self._tamano

  def __iter__(self):
    actual = self.cabeza
    while actual:
      yield actual.vehiculo
      actual = actual.siguiente


class PilaVentas:
  """Pila (LIFO) del historial de ventas: la cima es la venta más reciente."""

  def __init__(self):
    self.elementos = []

  def apilar_venta(self, venta):
    """Inserta una venta en la cima de la pila"""
    self.elementos.append(venta)

  def desapilar_venta(self):
    """Saca la venta de la cima si existe"""
    if not self.esta_vacia():
      return self.elementos.pop()
    return None

  def obtener_ultima_venta(self):
    """Retorna la cima sin eliminarla"""
    if not self.esta_vacia():
      return self.elementos[-1]
    return None

  def esta_vacia(self):
    return len(self.elementos) == 0

  def tamano(self) -> int:
    return len(self.elementos)

  def listar_desde_cima(self):
    """Ventas de la más reciente a la más antigua (sin modificar la pila)."""
    return list(reversed(self.elementos))
