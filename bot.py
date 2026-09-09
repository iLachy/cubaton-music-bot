import re
import requests
from bs4 import BeautifulSoup

# ============================================================
# DIAGNÓSTICO INDEPENDIENTE DE QOBUZ
# NO PUBLICA NADA
# NO MODIFICA state/releases.json
# ============================================================

CANCIONES = [
    {
        "titulo": "Pal Piso",
        "artistas": ["LA R", "Musteerifa", "Vittorio Di Benedetto"],
        "video_id": "AU_l1Rn_nJI",
    },
    {
        "titulo": "Las Ganas",
        "artistas": ["Payaso x Ley", "Musteerifa"],
        "video_id": None,
    },
    {
        "titulo": "LE DI",
        "artistas": ["Los Dele"],
        "video_id": None,
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def normalizar(texto):
    texto = str(texto or "").casefold()
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    return " ".join(texto.split())


def puntuacion_coincidencia(titulo_objetivo, artistas_objetivo, titulo, artistas):
    objetivo_titulo = normalizar(titulo_objetivo)
    resultado_titulo = normalizar(titulo)

    score = 0

    if objetivo_titulo and objetivo_titulo == resultado_titulo:
        score += 60
    elif objetivo_titulo and (
        objetivo_titulo in resultado_titulo
        or resultado_titulo in objetivo_titulo
    ):
        score += 35

    resultado_artistas = normalizar(" ".join(artistas))

    for artista in artistas_objetivo:
        artista_norm = normalizar(artista)
        if artista_norm and artista_norm in resultado_artistas:
            score += 20

    return score


def extraer_resultados_google(html):
    soup = BeautifulSoup(html, "html.parser")
    resultados = []

    for enlace in soup.select("a"):
        href = enlace.get("href", "")
        texto = " ".join(enlace.stripped_strings)

        if "qobuz.com" not in href:
            continue

        if not texto:
            continue

        if "/album/" not in href and "/interpreter/" not in href:
            continue

        resultados.append({
            "texto": texto,
            "url": href,
        })

    vistos = set()
    unicos = []

    for resultado in resultados:
        clave = resultado["url"]
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(resultado)

    return unicos


def analizar_pagina_qobuz(url):
    respuesta = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")
    texto = " ".join(soup.stripped_strings)

    fecha = ""
    patrones = [
        r"Released on (\d{1,2}/\d{1,2}/\d{2,4})",
        r"Released (?:on )?(\d{1,2}/\d{1,2}/\d{2,4})",
        r"Publicado el (\d{1,2}/\d{1,2}/\d{2,4})",
        r"publicado el (\d{1,2}/\d{1,2}/\d{2,4})",
        r"Sarà pubblicato il (\d{1,2}/\d{1,2}/\d{2,4})",
        r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            fecha = match.group(1)
            break

    return {
        "fecha": fecha,
        "texto": texto,
    }


def buscar_cancion(cancion):
    titulo = cancion["titulo"]
    artistas = cancion["artistas"]

    consultas = [
        f'site:qobuz.com/album/ "{titulo}" "{artistas[0]}"',
        f'site:qobuz.com/album/ "{titulo}" ' + " ".join(f'"{a}"' for a in artistas),
        f'site:qobuz.com "{titulo}" "{artistas[0]}"',
    ]

    resultados = []
    vistos = set()

    for consulta in consultas:
        print(f"\nConsulta: {consulta}")

        try:
            respuesta = requests.get(
                "https://www.google.com/search",
                params={"q": consulta},
                headers=HEADERS,
                timeout=30,
            )
            respuesta.raise_for_status()
        except Exception as error:
            print(f"ERROR en la consulta: {error}")
            continue

        encontrados = extraer_resultados_google(respuesta.text)
        print(f"Resultados Qobuz candidatos: {len(encontrados)}")

        for encontrado in encontrados:
            url = encontrado["url"]
            if url in vistos:
                continue
            vistos.add(url)
            resultados.append(encontrado)

    resultados_puntuados = []

    for resultado in resultados:
        texto = resultado["texto"]
        score = puntuacion_coincidencia(
            titulo,
            artistas,
            texto,
            [],
        )
        resultados_puntuados.append((score, resultado))

    resultados_puntuados.sort(key=lambda item: item[0], reverse=True)

    print(f"\nCandidatos únicos finales: {len(resultados_puntuados)}")

    for indice, (score, resultado) in enumerate(resultados_puntuados[:10], start=1):
        print("\n" + "-" * 70)
        print(f"CANDIDATO #{indice}")
        print(f"Puntuación: {score}")
        print(f"Texto:     {resultado['texto'][:500]}")
        print(f"URL:       {resultado['url']}")

        try:
            datos = analizar_pagina_qobuz(resultado["url"])
            print(f"Fecha detectada: {datos['fecha'] or '(no detectada)'}")
        except Exception as error:
            print(f"Error leyendo página Qobuz: {error}")


def main():
    print("=" * 70)
    print("DIAGNÓSTICO INDEPENDIENTE DE QOBUZ")
    print("NO PUBLICA NADA")
    print("NO MODIFICA state/releases.json")
    print("=" * 70)

    for cancion in CANCIONES:
        print("\n" + "=" * 70)
        print(f"CANCIÓN: {cancion['titulo']}")
        print("=" * 70)
        print(f"Artistas: {', '.join(cancion['artistas'])}")
        if cancion.get("video_id"):
            print(f"Video ID: {cancion['video_id']}")
        buscar_cancion(cancion)

    print("\n" + "=" * 70)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 70)


if __name__ == "__main__":
    main()
