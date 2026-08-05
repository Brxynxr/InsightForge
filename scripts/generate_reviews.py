import random

import pandas as pd
from faker import Faker


def generar_resenas_excel(
    nombre_archivo: str = "resenas_productos_50k.xlsx", num_filas: int = 50000
) -> str:
    """Genera un archivo Excel con reseñas falsas en español para testing."""
    print(f"Generando {num_filas} registros fake en español...")

    fake = Faker("es_ES")

    productos_cat = [
        "Audífonos Bluetooth Wireless",
        "Smartphone Pro Max 256GB",
        "Laptop Gamer 15.6''",
        "Reloj Inteligente Sport",
        "Cámara Digital 4K",
        "Teclado Mecánico RGB",
        "Monitor LED 27'' Curved",
        "Silla Ergonómica Oficina",
        "Cafetera Automática Express",
        "Aspiradora Robot Robotik",
        "Mochila Antirrobo Impermeable",
        "Parlante Portátil Waterproof",
    ]

    plantillas_resenas = [
        "Excelente producto, superó mis expectativas.",
        "Llegó a tiempo y en perfecto estado. Muy recomendado.",
        "La calidad del material es aceptable por el precio.",
        "No me gustó la calidad del producto, esperaba más.",
        "Pésimo servicio de entrega, llegó dañado.",
        "Funciona muy bien, lo uso todos los días.",
        "Buen diseño y materiales, aunque podría ser un poco más barato.",
        "Cumple con lo prometido en la descripción.",
        "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil.",
        "El botón de guardar no responde cuando estoy en la pantalla de configuración.",
        "La notificación push llega con minutos de retraso y a veces no llega.",
        "Se traba al cargar el inventario con más de 500 productos.",
        "El login con huella dactilar falla constantemente en Android 14.",
        "No puedo exportar los reportes a PDF, me sale error 500.",
        "La cámara del escáner de códigos no enfoca bien en ambientes con poca luz.",
        "El diseño es intuitivo pero le falta un modo oscuro.",
        "Cuando actualizo la app se pierden todos mis datos locales.",
        "El soporte técnico tarda semanas en responder.",
        "La sincronización entre dispositivos no funciona correctamente.",
        "La app consume demasiada batería en segundo plano.",
    ]

    data = []

    for _ in range(num_filas):
        id_cliente = fake.uuid4()[:8].upper()
        cliente = fake.name()
        ciudad = fake.city()
        producto = random.choice(productos_cat)

        # 25% de reseñas vacías (simula datos faltantes)
        if random.random() < 0.25:
            resena = ""
        else:
            resena = f"{random.choice(plantillas_resenas)} {fake.sentence(nb_words=6)}"

        data.append(
            {
                "id_cliente": id_cliente,
                "cliente": cliente,
                "ciudad": ciudad,
                "producto": producto,
                "reseña": resena,
            }
        )

    df = pd.DataFrame(data)
    df.to_excel(nombre_archivo, index=False, engine="openpyxl")
    print(f"Archivo creado: {nombre_archivo} ({num_filas} registros)")
    return nombre_archivo
