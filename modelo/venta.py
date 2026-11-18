import math
from datetime import datetime

from modelo.cliente import Cliente
from modelo.vehiculo import Vehiculo

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class Venta:

  def __init__(
      self,
      id_venta: str,
      cliente: Cliente,
      vehiculo: Vehiculo,
      precio_venta: float,
      fecha: datetime = None,
  ):
    precio_venta = float(precio_venta)
    if not math.isfinite(precio_venta) or precio_venta <= 0:
      raise ValueError("El precio de venta debe ser mayor a cero.")
    self.id_venta = id_venta
    self.fecha = fecha or datetime.now().replace(microsecond=0)
    self.cliente = cliente
    self.vehiculo = vehiculo
    self.precio_venta = precio_venta

  def generar_recibo(self) -> str:
    """Devuelve el recibo como texto (se muestra en la interfaz)."""
    lineas = [
        f"--- RECIBO DE VENTA [{self.id_venta}] ---",
        f"Fecha: {self.fecha.strftime('%d/%m/%Y %H:%M')}",
        (
            f"Cliente: {self.cliente.get_nombre()} (Cédula:"
            f" {self.cliente.get_cedula()})"
        ),
        (
            f"Vehículo: {self.vehiculo.get_marca()}"
            f" {self.vehiculo.get_modelo()} [VIN: {self.vehiculo.get_vin()}]"
        ),
        f"Precio base: ${self.vehiculo.get_precio_base():,.2f}",
        f"Precio de Venta Final: ${self.precio_venta:,.2f}",
    ]
    return "\n".join(lineas)
