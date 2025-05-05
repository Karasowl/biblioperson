import os
import sys
import json
import requests
import argparse
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración
API_LOCAL_URL = "http://localhost:5000/api"
NUM_RESULTADOS_DEFAULT = 5

# Clase base para los LLMs
class LLMProvider:
    def generate_content(self, prompt: str) -> str:
        raise NotImplementedError("Las subclases deben implementar este método")

# Implementación para Google Gemini
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=api_key)
        except ImportError:
            print("Error: No se pudo importar la librería 'google.generativeai'.")
            print("Por favor, instálala con: pip install google-generativeai")
            sys.exit(1)
            
    def generate_content(self, prompt: str) -> str:
        model = self.genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text

# Implementación para OpenAI
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            print("Error: No se pudo importar la librería 'openai'.")
            print("Por favor, instálala con: pip install openai")
            sys.exit(1)
            
    def generate_content(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente que genera contenido basado en los textos proporcionados."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

# Función para buscar contenido semánticamente relevante
def buscar_contenido_semantico(query: str, num_resultados: int = 5) -> List[Dict[str, Any]]:
    url = f"{API_LOCAL_URL}/busqueda/semantica"
    params = {
        "texto": query,
        "por_pagina": num_resultados
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanzar excepción si hay error HTTP
        data = response.json()
        return data.get("resultados", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API local: {e}")
        print("¿Está ejecutándose el servidor Flask en http://localhost:5000?")
        sys.exit(1)

# Función para construir el prompt
def construir_prompt(tema: str, contenidos: List[Dict[str, Any]], tipo_contenido: str, estilo: Optional[str] = None) -> str:
    # Extraer los textos de los resultados
    textos_contexto = [f"Fragmento {i+1}:\n\"{item['contenido']}\"\n" 
                      for i, item in enumerate(contenidos)]
    
    # Seleccionar instrucciones según tipo de contenido
    instrucciones_tipo = {
        "post": "Escribe un post para redes sociales",
        "articulo": "Escribe un artículo detallado",
        "guion": "Escribe un guion para un video o presentación",
        "resumen": "Crea un resumen conciso de las ideas principales",
        "analisis": "Realiza un análisis profundo del tema"
    }.get(tipo_contenido.lower(), "Escribe un texto")
    
    # Instrucciones de estilo
    instrucciones_estilo = ""
    if estilo:
        instrucciones_estilo = f"Utiliza un estilo {estilo}. "
    
    # Construir el prompt completo
    prompt = f"""
# TAREA
Actúa como un asistente de escritura experto. {instrucciones_tipo} sobre el tema: "{tema}".

# CONTEXTO
Los siguientes son fragmentos de texto auténticos relacionados con el tema. Utiliza EXCLUSIVAMENTE la información de estos fragmentos como base para tu respuesta:

{chr(10).join(textos_contexto)}

# INSTRUCCIONES ESPECÍFICAS
- Utiliza ÚNICAMENTE la información proporcionada en los fragmentos.
- Mantén el tono y perspectiva que se refleja en los textos originales.
- {instrucciones_estilo}Sé conciso pero informativo.
- No añadas información que no esté presente en los fragmentos proporcionados.
- No menciones que estás basándote en fragmentos o que tienes limitaciones.
- Finaliza con una reflexión o pregunta que invite a la interacción.

# RESPUESTA
"""
    
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Generador de contenido basado en RAG para Biblioteca Personal")
    parser.add_argument("tema", help="Tema sobre el que generar contenido")
    parser.add_argument("--tipo", "-t", default="post", choices=["post", "articulo", "guion", "resumen", "analisis"],
                      help="Tipo de contenido a generar (por defecto: post)")
    parser.add_argument("--estilo", "-e", help="Estilo de escritura (ej: formal, conversacional, académico)")
    parser.add_argument("--llm", "-l", default="gemini", choices=["gemini", "openai"], 
                      help="Proveedor de LLM a utilizar (por defecto: gemini)")
    parser.add_argument("--resultados", "-r", type=int, default=NUM_RESULTADOS_DEFAULT,
                      help=f"Número de resultados a recuperar (por defecto: {NUM_RESULTADOS_DEFAULT})")
    parser.add_argument("--solo-prompt", "-p", action="store_true",
                      help="Mostrar solo el prompt sin realizar la generación")
    
    args = parser.parse_args()
    
    # Verificar las claves API
    llm_provider = None
    if not args.solo_prompt:
        if args.llm == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Error: No se encontró la clave API para Gemini.")
                print("Por favor, agrega GEMINI_API_KEY=tu_clave en el archivo .env")
                sys.exit(1)
            llm_provider = GeminiProvider(api_key)
        elif args.llm == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("Error: No se encontró la clave API para OpenAI.")
                print("Por favor, agrega OPENAI_API_KEY=tu_clave en el archivo .env")
                sys.exit(1)
            llm_provider = OpenAIProvider(api_key)
    
    # Paso 1: Recuperar contenido relevante
    print(f"Buscando información sobre: '{args.tema}'...")
    resultados = buscar_contenido_semantico(args.tema, args.resultados)
    
    if not resultados:
        print("No se encontraron resultados relevantes. Intenta con otro tema o amplía tu búsqueda.")
        sys.exit(1)
    
    print(f"Se encontraron {len(resultados)} fragmentos relevantes.\n")
    
    # Paso 2: Construir el prompt
    prompt = construir_prompt(args.tema, resultados, args.tipo, args.estilo)
    
    if args.solo_prompt:
        print("\n=== PROMPT GENERADO ===\n")
        print(prompt)
        sys.exit(0)
    
    # Paso 3: Generar contenido
    print(f"Generando {args.tipo} con {args.llm.upper()}...")
    contenido_generado = llm_provider.generate_content(prompt)
    
    # Paso 4: Mostrar resultados
    print("\n=== CONTENIDO GENERADO ===\n")
    print(contenido_generado)
    print("\n===========================\n")

if __name__ == "__main__":
    main() 