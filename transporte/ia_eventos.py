from groq import Groq
from django.conf import settings



client = Groq(api_key=settings.GROQ_API_KEY)


def analizar_parada(viaje, duracion, ubicacion):

    prompt = f"""
    Analiza el siguiente evento logístico detectado en un sistema de monitoreo de transporte.

    Ruta: {viaje.origen} - {viaje.destino}
    Chofer: {viaje.chofer}
    Vehículo: {viaje.vehiculo}

    Evento detectado:
    Vehículo detenido durante {duracion} minutos
    Ubicación aproximada: {ubicacion}

    Genera un breve análisis en 5 lineas como máximo explicando posibles causas operativas de esta detención.
    """

    respuesta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )

    return respuesta.choices[0].message.content