#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shodan AI Stable - Búsquedas en Shodan usando lenguaje natural

Uso básico:
    python3 shodan_ai_stable.py "cámaras ip en chile"
    python3 shodan_ai_stable.py -h
    python3 shodan_ai_stable.py -V

Características:
    - Traduce preguntas en lenguaje natural a queries de Shodan.
    - Usa OpenAI si se configura OPENAI_API_KEY (opcional).
    - Si no hay IA, usa una traducción heurística estable.
    - Instala automáticamente las dependencias (shodan, openai) si faltan.
    - Guarda SHODAN_API_KEY y OPENAI_API_KEY en un archivo de configuración opcional.
"""

import sys
import os
import json
import subprocess
from typing import Dict, Any

CONFIG_FILE = os.path.expanduser("~/.shodan_ai_config.json")


# ───────────────────── Utilidades de configuración ─────────────────────

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            # En Windows puede fallar chmod, no es crítico
            pass
    except Exception as e:
        print(f"⚠ No se pudo guardar configuración: {e}")


def install_dependency(package: str) -> bool:
    """
    Intenta instalar un paquete con pip. Retorna True si se instala bien.
    """
    print(f"📦 Falta la librería '{package}'.")
    resp = input(f"¿Deseas instalar '{package}' ahora? (s/n): ").strip().lower()
    if resp not in ("s", "si", "sí", "y", "yes"):
        print(f"⚠ No se instaló '{package}'.")
        return False

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✔ '{package}' instalada correctamente.\n")
        return True
    except Exception as e:
        print(f"❌ No se pudo instalar '{package}': {e}")
        print("   Instálala manualmente, por ejemplo:")
        print(f"   {sys.executable} -m pip install {package}")
        return False


def ensure_shodan_installed() -> bool:
    try:
        import shodan  # noqa
        return True
    except ImportError:
        return install_dependency("shodan")


def ensure_openai_installed() -> bool:
    try:
        import openai  # noqa
        return True
    except ImportError:
        return install_dependency("openai")


# ───────────────────── Gestión de API Keys ─────────────────────

def get_shodan_key(config: Dict[str, Any]) -> str:
    """
    Obtiene la SHODAN_API_KEY desde:
    1. Variables de entorno
    2. Archivo de configuración
    3. Pregunta interactiva
    """
    env_key = os.environ.get("SHODAN_API_KEY")
    if env_key:
        return env_key

    if config.get("SHODAN_API_KEY"):
        return config["SHODAN_API_KEY"]

    print("\n🔐 Configuración de SHODAN_API_KEY")
    print("   Esta clave se usa EXCLUSIVAMENTE para conectar con la API de Shodan.")
    print("   No es lo mismo que la API de OpenAI.\n")
    print("   Para obtenerla:")
    print("   1. Crea una cuenta en https://account.shodan.io/")
    print("   2. Ve a 'My Account' y copia tu API Key.\n")

    key = input("Ingresa tu SHODAN_API_KEY: ").strip()
    if not key:
        print("❌ No se puede continuar sin SHODAN_API_KEY.")
        sys.exit(1)

    resp = input("¿Deseas guardar esta SHODAN_API_KEY para futuras ejecuciones? (s/n): ").strip().lower()
    if resp in ("s", "si", "sí", "y", "yes"):
        config["SHODAN_API_KEY"] = key
        save_config(config)

    return key


def get_openai_key(config: Dict[str, Any]) -> str:
    """
    Obtiene OPENAI_API_KEY de:
    1. Variables de entorno
    2. Archivo de configuración
    3. Pregunta interactiva
    Si el usuario no quiere usar OpenAI, retorna cadena vacía.
    """
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key

    if config.get("OPENAI_API_KEY"):
        return config["OPENAI_API_KEY"]

    print("\n🤖 Opcional: Integración con OpenAI para mejorar la traducción")
    resp = input("¿Quieres usar OpenAI para traducir las preguntas a queries de Shodan? (s/n): ").strip().lower()
    if resp not in ("s", "si", "sí", "y", "yes"):
        print("ℹ Se usará el modo heurístico sin IA.\n")
        return ""

    print("\n🔐 Configuración de OPENAI_API_KEY")
    print("   Esta clave es para el proveedor de IA (OpenAI), NO para Shodan.")
    print("   Para obtenerla:")
    print("   1. Ve a https://platform.openai.com/")
    print("   2. Crea una cuenta si no tienes.")
    print("   3. Genera una API key en https://platform.openai.com/api-keys\n")

    key = input("Ingresa tu OPENAI_API_KEY (o deja vacío para cancelar): ").strip()
    if not key:
        print("ℹ No se configuró OpenAI. Se usará modo heurístico.\n")
        return ""

    resp = input("¿Deseas guardar esta OPENAI_API_KEY para futuras ejecuciones? (s/n): ").strip().lower()
    if resp in ("s", "si", "sí", "y", "yes"):
        config["OPENAI_API_KEY"] = key
        save_config(config)

    return key


# ───────────────────── Traducción de preguntas ─────────────────────

def translate_query_heuristic(question: str) -> Dict[str, Any]:
    """
    Traducción simple pero robusta, sin IA.
    """
    q = question.lower()
    parts = []

    # Productos comunes
    prod_map = {
        "cisco": "product:cisco",
        "apache": "product:apache",
        "nginx": "product:nginx",
        "mikrotik": "product:mikrotik",
        "rdp": "port:3389",
        "ssh": "port:22",
        "ftp": "port:21",
    }
    for word, expr in prod_map.items():
        if word in q:
            parts.append(expr)

    # Países comunes (puedes ampliar)
    country_map = {
        "chile": "CL",
        "argentina": "AR",
        "mexico": "MX",
        "méxico": "MX",
        "españa": "ES",
        "peru": "PE",
        "perú": "PE",
        "colombia": "CO",
        "brasil": "BR",
        "uruguay": "UY",
    }
    for name, code in country_map.items():
        if name in q:
            parts.append(f"country:{code}")

    if not parts:
        query = " ".join(q.split())
    else:
        query = " ".join(parts)

    return {
        "query": query.strip() if query.strip() else q,
        "explanation": "Traducción heurística sin IA."
    }


def translate_query_openai(question: str, api_key: str) -> Dict[str, Any]:
    """
    Usa OpenAI para traducir la pregunta a una query Shodan.
    Si algo falla, cae a heurística.
    """
    if not api_key:
        return translate_query_heuristic(question)

    if not ensure_openai_installed():
        return translate_query_heuristic(question)

    try:
        from openai import OpenAI
    except ImportError:
        return translate_query_heuristic(question)

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Convierte la pregunta del usuario en una query de Shodan. "
                        "Usa filtros como country:, port:, product:, org:, etc. "
                        "Responde SOLO con la query, sin explicación adicional."
                    )
                },
                {"role": "user", "content": question}
            ],
            temperature=0.0
        )
        query = resp.choices[0].message.content.strip()
        if not query:
            return translate_query_heuristic(question)
        return {
            "query": query,
            "explanation": "Traducción usando OpenAI (gpt-4o-mini)."
        }
    except Exception as e:
        print(f"⚠ OpenAI falló ({e}). Se usará traducción heurística.\n")
        return translate_query_heuristic(question)


def translate_query(question: str, openai_key: str) -> Dict[str, Any]:
    if openai_key:
        return translate_query_openai(question, openai_key)
    return translate_query_heuristic(question)


# ───────────────────── Shodan ─────────────────────

def search_shodan(api_key: str, query: str):
    """
    Ejecuta la búsqueda en Shodan.
    Retorna (results, error_str). Si error_str no es None, es el motivo real.
    """
    import shodan
    api = shodan.Shodan(api_key)
    try:
        results = api.search(query)
        return results, None
    except shodan.APIError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)


def format_results(question: str, tdata: Dict[str, Any], results: Dict[str, Any], error: str) -> None:
    print("\n" + "=" * 80)
    print(f"PREGUNTA: {question}")
    print(f"QUERY SHODAN: {tdata['query']}")
    print(f"ORIGEN QUERY: {tdata['explanation']}")
    print("=" * 80 + "\n")

    if error:
        print("❌ ERROR REAL DEVUELTO POR LA API DE SHODAN:")
        print(f"   {error}\n")
        return

    if not results or results.get("total", 0) == 0:
        print("⚠ No hay resultados.")
        print("   Explicación real: Shodan respondió correctamente, pero no encontró")
        print("   coincidencias para la query generada. Prueba ajustar filtros, producto")
        print("   o país, o revisar si la búsqueda es demasiado específica.\n")
        return

    total = results.get("total", 0)
    print(f"📊 Total de resultados: {total}\n")

    matches = results.get("matches", [])
    if not matches:
        print("⚠ La respuesta de Shodan no contiene 'matches', posiblemente por un cambio")
        print("   en la API o por un tipo de respuesta distinto.\n")
        return

    print("🔍 Primeros resultados:\n")
    for i, item in enumerate(matches[:10], start=1):
        ip = item.get("ip_str", "N/A")
        port = item.get("port", "N/A")
        org = item.get("org", "N/A")
        loc = item.get("location") or {}
        country = loc.get("country_name", "N/A")
        city = loc.get("city", "")
        if city:
            city = f" - {city}"
        print(f"{i}. {ip}:{port} | {org} | {country}{city}")
    print("")


# ───────────────────── Ayuda y modo -V ─────────────────────

def show_help() -> None:
    help_text = """
Uso:
  python3 shodan_ai_stable.py "pregunta en lenguaje natural"
  python3 shodan_ai_stable.py -h
  python3 shodan_ai_stable.py --help
  python3 shodan_ai_stable.py -V
  python3 shodan_ai_stable.py --variable

Ejemplos:
  python3 shodan_ai_stable.py "cuantos dispositivos cisco hay en argentina"
  python3 shodan_ai_stable.py "camaras ip en chile con puerto 80 abierto"
  python3 shodan_ai_stable.py "servidores apache en españa"

Descripción rápida:
  - Te pide SHODAN_API_KEY la primera vez (y ofrece guardarla).
  - Opcionalmente puede usar OpenAI para traducir mejor la pregunta.
  - Si no se usa IA, aplica reglas heurísticas básicas.
  - Muestra el motivo real cuando la API devuelve error.
  - Si no hay resultados, te lo dice explícitamente y sin inventar causas.
"""
    print(help_text)


def show_variable_help() -> None:
    text = """
Guía para poder ejecutar el script desde cualquier parte (opcional):

1) Renombra el archivo a algo corto si quieres, por ejemplo:
   shodan-ai.py

2) Asegúrate de que tenga permisos de ejecución (Linux/macOS):
   chmod +x shodan-ai.py

3) Opciones:

   a) Alias en Linux/macOS (bash/zsh):
      - Abre tu archivo de configuración (~/.bashrc o ~/.zshrc) y agrega:
          alias shodan-ai='python3 /ruta/completa/shodan-ai.py'
      - Luego recarga el archivo:
          source ~/.bashrc
        o:
          source ~/.zshrc
      - Podrás ejecutar:
          shodan-ai "camaras ip en chile"

   b) Agregar a PATH en Linux/macOS:
      - Crea un directorio para tus scripts si no existe:
          mkdir -p $HOME/bin
      - Copia el script ahí:
          cp shodan-ai.py $HOME/bin/
      - Agrega a tu ~/.bashrc o ~/.zshrc:
          export PATH="$HOME/bin:$PATH"
      - Recarga el archivo:
          source ~/.bashrc
        o:
          source ~/.zshrc

   c) Windows (CMD / PowerShell):
      - Copia el script a una carpeta, por ejemplo:
          C:\\tools\\shodan-ai\\shodan-ai.py
      - Agrega esa carpeta al PATH del sistema o de usuario:
          Panel de control → Sistema → Configuración avanzada →
          Variables de entorno → Editar PATH
      - Luego podrás ejecutar:
          python C:\\tools\\shodan-ai\\shodan-ai.py "camaras ip en chile"

Esta opción (-V / --variable) no modifica nada automáticamente,
solo te explica cómo hacerlo tú, para mantener el control total.
"""
    print(text)


# ───────────────────── Main ─────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("❌ Debes proporcionar una pregunta o usar -h para ayuda.\n")
        show_help()
        sys.exit(1)

    arg1 = sys.argv[1]

    if arg1 in ("-h", "--help"):
        show_help()
        sys.exit(0)

    if arg1 in ("-V", "--variable"):
        show_variable_help()
        sys.exit(0)

    # A partir de aquí asumimos que es una consulta
    if not ensure_shodan_installed():
        sys.exit(1)

    config = load_config()
    shodan_key = get_shodan_key(config)
    openai_key = get_openai_key(config)

    question = " ".join(sys.argv[1:]).strip()
    print(f"\n🤖 Procesando pregunta: {question}\n")

    # Traducción
    tdata = translate_query(question, openai_key)

    # Búsqueda en Shodan
    results, error = search_shodan(shodan_key, tdata["query"])

    # Mostrar resultados
    format_results(question, tdata, results, error)


if __name__ == "__main__":
    main()
