import json

# ------------------ CONFIGURACIÓN ------------------

# Diccionario con precios por metro cuadrado según material
PRECIOS_MATERIALES = {
    "melamina": 8000,   # precio por m2
    "mdf": 6000,
    "madera": 12000
}

# Porcentaje de desperdicio aplicado al total de materiales
DESPERDICIO_PORCENTAJE = 0.10  # 10%


# ------------------ MODELOS ------------------

# Medidas estándar de una placa (en cm)
PLACA_ANCHO = 275
PLACA_ALTO = 183


# Representa una placa de madera donde se van acomodando piezas
class Placa:
    def __init__(self):
        self.filas = []  # lista de filas, cada fila contiene piezas
        self.alto_usado = 0  # cuánto alto de la placa ya está ocupado

    # Verifica si una pieza entra en una fila existente (horizontalmente)
    def puede_agregar_en_fila(self, fila, pieza):
        ancho_usado = sum(p.ancho for p in fila)  # suma del ancho ocupado
        return ancho_usado + pieza.ancho <= PLACA_ANCHO

    # Verifica si hay espacio vertical para agregar una nueva fila
    def puede_agregar(self, pieza):
        return self.alto_usado + pieza.alto <= PLACA_ALTO

    # Intenta agregar una pieza a la placa
    def agregar_pieza(self, pieza):
        # 1. Intentar meter en filas ya existentes
        for fila in self.filas:
            if self.puede_agregar_en_fila(fila, pieza):
                fila.append(pieza)
                return True

        # 2. Si no entra, intentar crear una nueva fila
        if self.puede_agregar(pieza):
            self.filas.append([pieza])
            self.alto_usado += pieza.alto
            return True

        # 3. Si no entra, la placa ya está llena
        return False


# Función principal de optimización de corte
def optimizar_corte(piezas):
    # Ordena piezas de mayor a menor altura (mejora el aprovechamiento)
    piezas = sorted(piezas, key=lambda p: p.alto, reverse=True)

    placas = []  # lista de placas generadas

    # Recorre cada pieza e intenta ubicarla
    for pieza in piezas:
        colocada = False

        # Intenta colocarla en alguna placa existente
        for placa in placas:
            if placa.agregar_pieza(pieza):
                colocada = True
                break

        # Si no entra en ninguna, crea una nueva placa
        if not colocada:
            nueva = Placa()
            nueva.agregar_pieza(pieza)
            placas.append(nueva)

    return placas


# Representa una pieza individual del mueble
class Pieza:
    def __init__(self, nombre, ancho, alto, material):
        self.nombre = nombre
        self.ancho = ancho
        self.alto = alto
        self.material = material

    # Calcula el área en metros cuadrados
    def area_m2(self):
        return (self.ancho * self.alto) / 10000

    # Calcula el costo según el material
    def costo(self):
        precio_m2 = PRECIOS_MATERIALES.get(self.material, 0)
        return self.area_m2() * precio_m2


# Representa un mueble compuesto por múltiples piezas
class Mueble:
    def __init__(self, nombre):
        self.nombre = nombre
        self.piezas = []
        self.herrajes = 0
        self.mano_obra = 0

    # Agrega una pieza al mueble
    def agregar_pieza(self, pieza):
        self.piezas.append(pieza)

    # Suma el costo de todas las piezas
    def subtotal_materiales(self):
        return sum(p.costo() for p in self.piezas)

    # Calcula el desperdicio
    def desperdicio(self):
        return self.subtotal_materiales() * DESPERDICIO_PORCENTAJE

    # Calcula el total final
    def total(self):
        return (
            self.subtotal_materiales()
            + self.desperdicio()
            + self.herrajes
            + self.mano_obra
        )


# ------------------ FUNCIONES ------------------

# Carga un mueble desde un archivo JSON
def cargar_desde_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mueble = Mueble(data["nombre"])

    # -------- PIEZAS DIRECTAS (compatibilidad con formato viejo) --------
    for p in data.get("piezas", []):
        pieza = Pieza(
            p["nombre"],
            p["ancho"],
            p["alto"],
            p.get("material", data.get("material_principal", "melamina"))
        )
        mueble.agregar_pieza(pieza)

    # -------- FUNCIÓN INTERNA PARA BISAGRAS --------
    def calcular_bisagras(alto):
        """
        Regla:
        - <= 60 cm → 2 bisagras
        - > 60 cm → 2 + 1 cada 30 cm extra
        """
        if alto <= 60:
            return 2

        extra = alto - 60
        adicionales = extra // 30
        return 2 + int(adicionales)

    total_bisagras = 0

    # -------- PUERTAS --------
    for puerta in data.get("puertas", []):
        cantidad = puerta.get("cantidad", 1)

        for _ in range(cantidad):
            pieza = Pieza(
                puerta["nombre"],
                puerta["ancho"],
                puerta["alto"],
                puerta.get("material", data.get("material_principal", "melamina"))
            )
            mueble.agregar_pieza(pieza)

            # calcular bisagras automáticamente
            total_bisagras += calcular_bisagras(puerta["alto"])

    # -------- HERRAJES --------
    herrajes_data = data.get("herrajes", {})

    # si viene precio de bisagra → calcular automático
    precio_bisagra = herrajes_data.get("precio_bisagra", 0)

    if precio_bisagra > 0:
        mueble.herrajes = total_bisagras * precio_bisagra
    else:
        # fallback a valor fijo (compatibilidad)
        mueble.herrajes = data.get("herrajes", 0)

    # -------- MANO DE OBRA --------
    mueble.mano_obra = data.get("mano_obra", 0)

    return mueble


# Muestra el presupuesto completo en consola
def mostrar_presupuesto(mueble):
    print(f"\n📦 PRESUPUESTO: {mueble.nombre}")
    print("-" * 40)

    # Detalle de piezas
    for p in mueble.piezas:
        print(f"{p.nombre}")
        print(f"  {p.ancho}x{p.alto} cm")
        print(f"  Material: {p.material}")
        print(f"  Área: {p.area_m2():.2f} m²")
        print(f"  Costo: ${p.costo():.2f}")
        print()

    subtotal = mueble.subtotal_materiales()
    desperdicio = mueble.desperdicio()
    total = mueble.total()

    # Resumen
    print("-" * 40)
    print(f"Subtotal materiales: ${subtotal:.2f}")
    print(f"Desperdicio ({DESPERDICIO_PORCENTAJE*100}%): ${desperdicio:.2f}")
    print(f"Herrajes: ${mueble.herrajes:.2f}")
    print(f"Mano de obra: ${mueble.mano_obra:.2f}")
    print("-" * 40)
    print(f"TOTAL: ${total:.2f}")


# Muestra cómo se distribuyen las piezas en las placas
def mostrar_optimizacion(placas):
    print("\n🪵 OPTIMIZACIÓN DE CORTE")
    print("=" * 40)

    for i, placa in enumerate(placas, 1):
        print(f"\nPlaca {i}:")
        for fila in placa.filas:
            fila_txt = " | ".join(f"{p.nombre}({p.ancho}x{p.alto})" for p in fila)
            print(f"  {fila_txt}")
 

# Guarda el presupuesto en un archivo de texto
def guardar_txt(mueble, filename="presupuesto.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PRESUPUESTO: {mueble.nombre}\n\n")

        for p in mueble.piezas:
            f.write(f"{p.nombre}\n")
            f.write(f"  {p.ancho}x{p.alto} cm\n")
            f.write(f"  Material: {p.material}\n")
            f.write(f"  Área: {p.area_m2():.2f} m²\n")
            f.write(f"  Costo: ${p.costo():.2f}\n\n")

        f.write(f"Subtotal: ${mueble.subtotal_materiales():.2f}\n")
        f.write(f"Desperdicio: ${mueble.desperdicio():.2f}\n")
        f.write(f"Herrajes: ${mueble.herrajes:.2f}\n")
        f.write(f"Mano de obra: ${mueble.mano_obra:.2f}\n")
        f.write(f"TOTAL: ${mueble.total():.2f}\n")


# ------------------ EJECUCIÓN ------------------

if __name__ == "__main__":
    # Ruta del archivo JSON
    ruta = "mueble.json"

    # Cargar datos
    mueble = cargar_desde_json(ruta)

    # Mostrar presupuesto
    mostrar_presupuesto(mueble)

    # Optimización de corte
    placas = optimizar_corte(mueble.piezas)
    mostrar_optimizacion(placas)

    # Guardar resultado en archivo
    guardar_txt(mueble)