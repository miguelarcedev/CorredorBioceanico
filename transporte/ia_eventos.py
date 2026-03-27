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


def analizar_viaje_completo(viaje, prompt_usuario=None):

    prompt = f"""
        Actuá como analista logístico profesional.

        Analizá el siguiente viaje:

        Ruta: {viaje.origen} - {viaje.destino}
        Chofer: {viaje.chofer}
        Vehículo: {viaje.vehiculo}

        Generá un informe estructurado con este formato EXACTO:

        Score: XX/100

        Eficiencia del viaje:
        (texto breve)

        Problemas detectados:
        - punto 1
        - punto 2

        Recomendaciones:
        - mejora 1
        - mejora 2

        Reglas:
        - Máximo 120 palabras
        - No inventar datos faltantes
        - Ser claro y profesional
        """

    if prompt_usuario:
        prompt += f"\n\nInstrucción adicional del usuario:\n{prompt_usuario}"

    respuesta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )

    return respuesta.choices[0].message.content
