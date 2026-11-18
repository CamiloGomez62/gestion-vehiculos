"""Pruebas de la lógica del programa (no abren la interfaz gráfica).

Ejecutar desde la carpeta del proyecto:
    python -m unittest discover -s pruebas -v
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from controlador.conexion import Conexion
from controlador.controlador import ControladorPrincipal, _a_decimal
from modelo.automovil import Automovil
from modelo.camion import Camion
from modelo.cliente import Cliente
from modelo.estructuras import ListaDoblementeEnlazadaVehiculos, PilaVentas
from modelo.moto import Moto
from modelo.vehiculo import Vehiculo
from modelo.venta import Venta

AUTO = {"puertas": "4", "combustible": "Gasolina", "camara": "Sí"}
MOTO = {"cilindraje": "250", "manubrio": "Naked", "abs": "No"}
CAMION = {"carga": "10.5", "ejes": "3", "carroceria": "Furgón"}


class BaseConBD(unittest.TestCase):

  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.ruta = Path(self._tmp.name) / "datos" / "prueba.db"
    self.ctrl = ControladorPrincipal(Conexion(self.ruta))

  def tearDown(self):
    self._tmp.cleanup()

  def auto(self, vin="VIN1", precio="35000"):
    return self.ctrl.guardar_vehiculo(vin, "Mazda", "CX-5", "2024", precio, "Auto", AUTO)

  def cliente(self, cedula="111", nombre="Ana", tel="555"):
    return self.ctrl.guardar_cliente(cedula, nombre, tel)


class PruebasBaseDeDatos(BaseConBD):

  def test_se_crea_el_archivo_y_las_tablas(self):
    self.assertTrue(self.ruta.exists())
    con = sqlite3.connect(self.ruta)
    tablas = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    self.assertTrue(
        {"clientes", "vehiculos", "detalles_auto", "detalles_moto",
         "detalles_camion", "ventas"} <= tablas
    )

  def test_abrir_dos_veces_no_borra_datos(self):
    self.auto()
    otro = ControladorPrincipal(Conexion(self.ruta))
    self.assertEqual(len(otro.consultar_vehiculos()), 1)

  def test_llaves_foraneas_activas(self):
    with self.assertRaises(sqlite3.IntegrityError):
      with self.ctrl.db.transaccion() as conn:
        conn.execute("INSERT INTO detalles_auto VALUES ('NOEXISTE', 4, 'x', 1)")


class PruebasVehiculos(BaseConBD):

  def test_guardar_los_tres_tipos_con_sus_datos_reales(self):
    self.assertTrue(self.auto()[0])
    self.assertTrue(self.ctrl.guardar_vehiculo("M1", "Yamaha", "R3", "2023", "9000", "Moto", MOTO)[0])
    self.assertTrue(self.ctrl.guardar_vehiculo("C1", "Volvo", "FH", "2022", "90000", "Camión", CAMION)[0])
    por_vin = {v.get_vin(): v for v in self.ctrl.consultar_vehiculos()}
    self.assertIsInstance(por_vin["VIN1"], Automovil)
    self.assertEqual(por_vin["VIN1"].get_num_puertas(), 4)
    self.assertTrue(por_vin["VIN1"].is_tiene_camara_reversa())
    self.assertEqual(por_vin["M1"].get_cilindraje(), 250)
    self.assertEqual(por_vin["M1"].get_tipo_manubrio(), "Naked")
    self.assertFalse(por_vin["M1"].is_tiene_abs())
    self.assertEqual(por_vin["C1"].get_capacidad_carga(), 10.5)
    self.assertEqual(por_vin["C1"].get_num_ejes(), 3)

  def test_vin_duplicado(self):
    self.auto()
    ok, msg = self.auto()
    self.assertFalse(ok)
    self.assertIn("Ya existe", msg)

  def test_vin_se_normaliza_a_mayusculas(self):
    self.auto("abc-123")
    self.assertEqual(self.ctrl.consultar_vehiculos()[0].get_vin(), "ABC-123")

  def test_validaciones(self):
    casos = [
        ("", "Mazda", "CX", "2024", "100", AUTO),
        ("V", "", "CX", "2024", "100", AUTO),
        ("V", "Mazda", "CX", "abc", "100", AUTO),
        ("V", "Mazda", "CX", "1800", "100", AUTO),
        ("V", "Mazda", "CX", "2024", "-5", AUTO),
        ("V", "Mazda", "CX", "2024", "0", AUTO),
        ("V", "Mazda", "CX", "2024", "nan", AUTO),
        ("V", "Mazda", "CX", "2024", "100", {**AUTO, "puertas": "9"}),
        ("V", "Mazda", "CX", "2024", "100", {**AUTO, "puertas": ""}),
        ("V !", "Mazda", "CX", "2024", "100", AUTO),
    ]
    for caso in casos:
      ok, msg = self.ctrl.guardar_vehiculo(*caso[:5], "Auto", caso[5])
      self.assertFalse(ok, caso)
      self.assertTrue(msg)
    self.assertEqual(self.ctrl.consultar_vehiculos(), [])

  def test_si_falla_el_detalle_no_queda_vehiculo_huerfano(self):
    # Se rompe a propósito la tabla de detalle para forzar un error real en
    # la SEGUNDA inserción: la primera (vehiculos) debe deshacerse.
    with self.ctrl.db.transaccion() as conn:
      conn.execute("DROP TABLE detalles_camion")
    ok, msg = self.ctrl.guardar_vehiculo("V1", "A", "B", "2024", "100", "Camión", CAMION)
    self.assertFalse(ok)
    self.assertIn("base de datos", msg)
    with self.ctrl.db.transaccion() as conn:
      self.assertEqual(conn.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0], 0)

  def test_eliminar(self):
    self.auto()
    self.assertTrue(self.ctrl.eliminar_vehiculo("vin1")[0])
    self.assertFalse(self.ctrl.eliminar_vehiculo("VIN1")[0])
    self.assertFalse(self.ctrl.eliminar_vehiculo("")[0])
    with self.ctrl.db.transaccion() as conn:
      self.assertEqual(conn.execute("SELECT COUNT(*) FROM detalles_auto").fetchone()[0], 0)

  def test_actualizar_precio(self):
    self.auto()
    self.assertTrue(self.ctrl.actualizar_precio_vehiculo("VIN1", "40.000.000")[0])
    self.assertEqual(self.ctrl.consultar_vehiculos()[0].get_precio_base(), 40000000)
    self.assertFalse(self.ctrl.actualizar_precio_vehiculo("VIN1", "-1")[0])
    self.assertFalse(self.ctrl.actualizar_precio_vehiculo("NOPE", "5")[0])

  def test_formatos_de_precio(self):
    self.assertEqual(_a_decimal("35000", "p"), 35000)
    self.assertEqual(_a_decimal("35.000.000", "p"), 35000000)
    self.assertEqual(_a_decimal("35,000.50", "p"), 35000.5)
    self.assertEqual(_a_decimal("35,50", "p"), 35.5)
    self.assertEqual(_a_decimal("$ 1.250.000,75", "p"), 1250000.75)
    for malo in ("abc", "", "1e5", "inf", "1.2.3x"):
      with self.assertRaises(ValueError):
        _a_decimal(malo, "p")


class PruebasClientes(BaseConBD):

  def test_guardar_y_listar(self):
    self.assertTrue(self.cliente()[0])
    clientes = self.ctrl.obtener_clientes()
    self.assertEqual([c.get_nombre() for c in clientes], ["Ana"])

  def test_duplicado_y_validaciones(self):
    self.cliente()
    self.assertIn("Ya existe", self.cliente()[1])
    self.assertFalse(self.cliente("22", "Luis", "555")[0])  # cédula muy corta
    self.assertFalse(self.cliente("222", "", "555")[0])
    self.assertFalse(self.cliente("222", "Luis", "abc")[0])


class PruebasVentas(BaseConBD):

  def preparar(self):
    self.auto("VIN1", "35000")
    self.auto("VIN2", "20000")
    self.cliente("111", "Ana", "555")
    self.cliente("222", "Luis", "666")

  def test_venta_ok_con_recibo_y_pila(self):
    self.preparar()
    ok, msg = self.ctrl.registrar_venta("111", "VIN1", "34000")
    self.assertTrue(ok, msg)
    venta = self.ctrl.ultima_venta()
    self.assertEqual(venta.id_venta, "V-0001")
    recibo = venta.generar_recibo()
    self.assertIn("Ana", recibo)
    self.assertIn("VIN1", recibo)
    self.assertIn("34,000.00", recibo)
    self.assertEqual([v.get_vin() for v in self.ctrl.obtener_vehiculos_disponibles()], ["VIN2"])

  def test_no_se_puede_vender_dos_veces(self):
    self.preparar()
    self.assertTrue(self.ctrl.registrar_venta("111", "VIN1", "34000")[0])
    ok, msg = self.ctrl.registrar_venta("222", "VIN1", "30000")
    self.assertFalse(ok)
    self.assertIn("ya fue vendido", msg)
    self.assertEqual(self.ctrl.historial_ventas_pila.tamano(), 1)

  def test_datos_inexistentes_o_invalidos(self):
    self.preparar()
    self.assertFalse(self.ctrl.registrar_venta("999", "VIN1", "1000")[0])
    self.assertFalse(self.ctrl.registrar_venta("111", "NOPE", "1000")[0])
    self.assertFalse(self.ctrl.registrar_venta("111", "VIN1", "abc")[0])
    self.assertFalse(self.ctrl.registrar_venta("111", "VIN1", "0")[0])
    self.assertTrue(self.ctrl.historial_ventas_pila.esta_vacia())

  def test_ids_consecutivos_aunque_existan_otros(self):
    self.preparar()
    self.ctrl.registrar_venta("111", "VIN1", "1000", id_venta="V-01")
    self.ctrl.registrar_venta("222", "VIN2", "1000")
    self.assertEqual(self.ctrl.ultima_venta().id_venta, "V-0002")

  def test_historial_es_pila_lifo_y_sobrevive_al_reiniciar(self):
    self.preparar()
    self.ctrl.registrar_venta("111", "VIN1", "1000")
    self.ctrl.registrar_venta("222", "VIN2", "2000")
    self.assertEqual([v.id_venta for v in self.ctrl.historial_ventas()], ["V-0002", "V-0001"])
    nuevo = ControladorPrincipal(Conexion(self.ruta))
    self.assertEqual(nuevo.historial_ventas_pila.tamano(), 2)
    self.assertEqual(nuevo.ultima_venta().id_venta, "V-0002")
    self.assertEqual(nuevo.ultima_venta().cliente.get_nombre(), "Luis")

  def test_anular_ultima_venta(self):
    self.preparar()
    self.assertFalse(self.ctrl.anular_ultima_venta()[0])
    self.ctrl.registrar_venta("111", "VIN1", "1000")
    self.ctrl.registrar_venta("222", "VIN2", "2000")
    ok, msg = self.ctrl.anular_ultima_venta()
    self.assertTrue(ok, msg)
    self.assertEqual(self.ctrl.ultima_venta().id_venta, "V-0001")
    self.assertEqual([v.get_vin() for v in self.ctrl.obtener_vehiculos_disponibles()], ["VIN2"])
    # tras anular, el VIN2 se puede volver a vender
    self.assertTrue(self.ctrl.registrar_venta("111", "VIN2", "1500")[0])

  def test_vehiculo_vendido_no_se_elimina_ni_cambia_de_precio(self):
    self.preparar()
    self.ctrl.registrar_venta("111", "VIN1", "1000")
    self.assertIn("venta registrada", self.ctrl.eliminar_vehiculo("VIN1")[1])
    self.assertFalse(self.ctrl.actualizar_precio_vehiculo("VIN1", "5")[0])
    self.assertEqual(len(self.ctrl.consultar_vehiculos()), 2)

  def test_la_base_impide_borrar_cliente_con_ventas(self):
    self.preparar()
    self.ctrl.registrar_venta("111", "VIN1", "1000")
    with self.assertRaises(sqlite3.IntegrityError):
      with self.ctrl.db.transaccion() as conn:
        conn.execute("DELETE FROM clientes WHERE cedula='111'")


class PruebasEstructuras(unittest.TestCase):

  def hacer(self, n):
    lista = ListaDoblementeEnlazadaVehiculos()
    for i in range(n):
      lista.agregar_vehiculo(Moto(f"M{i}", "Y", "R3", 2023, 1000, 250, "Naked", True))
    return lista

  def test_navegacion_adelante_y_atras(self):
    lista = self.hacer(3)
    self.assertEqual(lista.avanzar().vin, "M0")
    self.assertEqual(lista.avanzar().vin, "M1")
    self.assertEqual(lista.avanzar().vin, "M2")
    self.assertEqual(lista.avanzar().vin, "M2")  # tope
    self.assertEqual(lista.retroceder().vin, "M1")
    self.assertEqual(lista.ir_a("m0").vin, "M0")
    self.assertEqual(lista.retroceder().vin, "M0")  # tope
    self.assertEqual(len(lista), 3)

  def test_eliminar_en_cabeza_medio_y_cola(self):
    lista = self.hacer(4)
    self.assertTrue(lista.eliminar_por_vin("M0"))
    self.assertTrue(lista.eliminar_por_vin("M3"))
    self.assertTrue(lista.eliminar_por_vin("M1"))
    self.assertFalse(lista.eliminar_por_vin("M1"))
    self.assertEqual([v.vin for v in lista], ["M2"])
    self.assertIs(lista.cabeza, lista.cola)
    self.assertTrue(lista.eliminar_por_vin("M2"))
    self.assertTrue(lista.esta_vacia())
    self.assertIsNone(lista.avanzar())

  def test_pila(self):
    pila = PilaVentas()
    self.assertTrue(pila.esta_vacia())
    self.assertIsNone(pila.desapilar_venta())
    self.assertIsNone(pila.obtener_ultima_venta())
    pila.apilar_venta("a")
    pila.apilar_venta("b")
    self.assertEqual(pila.obtener_ultima_venta(), "b")
    self.assertEqual(pila.listar_desde_cima(), ["b", "a"])
    self.assertEqual(pila.desapilar_venta(), "b")
    self.assertEqual(pila.tamano(), 1)


class PruebasModelo(unittest.TestCase):

  def test_vehiculo_es_abstracto(self):
    with self.assertRaises(TypeError):
      Vehiculo("A", "m", "m", 2020, 1)

  def test_getters_y_setters_funcionan(self):
    c = Camion("C1", "Volvo", "FH", 2022, 90000, 10, 3, "Furgón")
    c.set_precio_base(95000)
    c.set_capacidad_carga(12)
    c.set_marca("Scania")
    self.assertEqual((c.get_precio_base(), c.get_capacidad_carga(), c.get_marca()), (95000, 12, "Scania"))
    with self.assertRaises(ValueError):
      c.set_precio_base(-1)
    with self.assertRaises(ValueError):
      c.set_capacidad_carga(0)
    self.assertEqual(c.get_precio_base(), 95000)  # no cambió

  def test_str_y_detalle(self):
    a = Automovil("A1", "Mazda", "CX-5", 2024, 35000, 4, "Gasolina", True)
    self.assertIn("A1", str(a))
    self.assertIn("4 puertas", a.detalle())
    cl = Cliente("111", "Ana", "555")
    self.assertIn("Ana", str(cl))
    cl.set_telefono("300 123")
    self.assertEqual(cl.get_telefono(), "300 123")

  def test_recibo(self):
    a = Automovil("A1", "Mazda", "CX-5", 2024, 35000, 4, "Gasolina", True)
    v = Venta("V-1", Cliente("111", "Ana", "555"), a, 34000)
    self.assertIn("RECIBO DE VENTA [V-1]", v.generar_recibo())
    with self.assertRaises(ValueError):
      Venta("V-2", Cliente("111", "Ana", "555"), a, 0)


if __name__ == "__main__":
  unittest.main()
