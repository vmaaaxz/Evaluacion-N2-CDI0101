
import requests
from getpass import getpass

GEOCODE_URL = "https://graphhopper.com/api/1/geocode"
ROUTE_URL = "https://graphhopper.com/api/1/route"

GALON_A_LITROS = 3.78541


def geocoding(location, api_key):
    """Obtiene las coordenadas de una ciudad mediante GraphHopper."""

    params = {
        "q": location,
        "limit": 1,
        "key": api_key
    }

    response = requests.get(
        GEOCODE_URL,
        params=params,
        timeout=30
    )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("La API de geocodificacion no devolvio JSON valido.")

    if response.status_code != 200:
        mensaje = data.get("message", response.text)
        raise RuntimeError(
            f"Error de geocodificacion HTTP {response.status_code}: {mensaje}"
        )

    hits = data.get("hits", [])

    if not hits:
        raise RuntimeError(
            f"No se encontraron resultados para: {location}"
        )

    hit = hits[0]
    point = hit["point"]

    nombre = hit.get("name", location)
    estado = hit.get("state", "")
    pais = hit.get("country", "")

    partes = [nombre]

    if estado and estado != nombre:
        partes.append(estado)

    if pais:
        partes.append(pais)

    nombre_completo = ", ".join(partes)

    print(f"Geocoding API Status: {response.status_code}")
    print(f"Ubicacion encontrada: {nombre_completo}")

    return {
        "lat": point["lat"],
        "lng": point["lng"],
        "name": nombre_completo
    }


def obtener_ruta(origen, destino, api_key, perfil):
    """Consulta GraphHopper para obtener la ruta."""

    params = [
        ("key", api_key),
        ("profile", perfil),
        ("point", f"{origen['lat']},{origen['lng']}"),
        ("point", f"{destino['lat']},{destino['lng']}"),
        ("locale", "es"),
        ("instructions", "true")
    ]

    response = requests.get(
        ROUTE_URL,
        params=params,
        timeout=60
    )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("La API de rutas no devolvio JSON valido.")

    if response.status_code != 200:
        mensaje = data.get("message", response.text)
        raise RuntimeError(
            f"Error de routing HTTP {response.status_code}: {mensaje}"
        )

    rutas = data.get("paths", [])

    if not rutas:
        raise RuntimeError("La API no encontro una ruta disponible.")

    print(f"Routing API Status: {response.status_code}")

    return rutas[0]


def mostrar_resultados(origen, destino, ruta, perfil, consumo):
    """Muestra distancia, duracion, combustible y narrativa."""

    distancia_km = ruta["distance"] / 1000
    tiempo_segundos = ruta["time"] / 1000

    horas = int(tiempo_segundos // 3600)
    minutos = int((tiempo_segundos % 3600) // 60)
    segundos = int(tiempo_segundos % 60)

    total_horas = tiempo_segundos / 3600
    total_minutos = tiempo_segundos / 60

    print("\n" + "=" * 55)
    print("RESULTADO DEL VIAJE")
    print("=" * 55)

    print(f"Ciudad de origen: {origen['name']}")
    print(f"Ciudad de destino: {destino['name']}")
    print(f"Perfil de transporte: {perfil}")
    print(f"Distancia: {distancia_km:.2f} km")

    print(
        f"Duracion del viaje: "
        f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    )

    print(f"Duracion total en horas: {total_horas:.2f}")
    print(f"Duracion total en minutos: {total_minutos:.2f}")
    print(f"Duracion total en segundos: {tiempo_segundos:.2f}")

    if perfil == "car":
        combustible_litros = distancia_km * consumo / 100

        print(f"Consumo configurado: {consumo:.2f} L/100 km")
        print(f"Combustible estimado: {combustible_litros:.2f} litros")
    else:
        print("Combustible: no aplica al perfil seleccionado.")

    print("\n" + "=" * 55)
    print("NARRATIVA DEL VIAJE")
    print("=" * 55)

    instrucciones = ruta.get("instructions", [])

    if instrucciones:
        for numero, instruccion in enumerate(instrucciones, start=1):
            texto = instruccion.get("text", "Continuar por la ruta")
            metros = instruccion.get("distance", 0)
            km = metros / 1000

            print(f"{numero:02d}. {texto} ({km:.2f} km)")
    else:
        print("La API no devolvio instrucciones para el recorrido.")

    print("=" * 55)


def main():
    print("=" * 55)
    print("EVALUACION PARCIAL 2 CDI0101")
    print("Consumo de API publica: GraphHopper")
    print("Escribe q o Quit para salir.")
    print("=" * 55)

    api_key = getpass("Ingresa tu API Key de GraphHopper: ").strip()

    if not api_key:
        print("Error: no ingresaste una API Key.")
        return

    while True:
        print("\nPerfiles disponibles: car, bike, foot")

        perfil = input(
            "Selecciona el perfil [car]: "
        ).strip().lower()

        if perfil in ("q", "quit"):
            print("Programa finalizado.")
            break

        if not perfil:
            perfil = "car"

        if perfil not in ("car", "bike", "foot"):
            print("Perfil no valido. Se utilizara car.")
            perfil = "car"

        origen_texto = input(
            "Starting Location [Santiago, Chile]: "
        ).strip()

        if origen_texto.lower() in ("q", "quit"):
            print("Programa finalizado.")
            break

        if not origen_texto:
            origen_texto = "Santiago, Chile"

        destino_texto = input(
            "Destination [La Serena, Chile]: "
        ).strip()

        if destino_texto.lower() in ("q", "quit"):
            print("Programa finalizado.")
            break

        if not destino_texto:
            destino_texto = "La Serena, Chile"

        consumo = 8.00

        if perfil == "car":
            entrada = input(
                "Consumo del vehiculo en L/100 km [8.00]: "
            ).strip()

            if entrada:
                try:
                    consumo = float(entrada)

                    if not 0 < consumo < 100:
                        raise ValueError

                except ValueError:
                    print(
                        "Consumo no valido. Se utilizara 8.00 L/100 km."
                    )
                    consumo = 8.00

        try:
            origen = geocoding(origen_texto, api_key)
            destino = geocoding(destino_texto, api_key)

            ruta = obtener_ruta(
                origen,
                destino,
                api_key,
                perfil
            )

            mostrar_resultados(
                origen,
                destino,
                ruta,
                perfil,
                consumo
            )

        except requests.exceptions.RequestException as error:
            print(f"Error de conexion con GraphHopper: {error}")

        except (RuntimeError, KeyError, TypeError, ValueError) as error:
            print(f"No se pudo completar el viaje: {error}")


if __name__ == "__main__":
    main()
