#!/usr/bin/env python3
"""
Script para instalar el modelo de spaCy en español necesario para la detección de autores.
"""

import subprocess
import sys

def install_spacy_model():
    """Instala el modelo de spaCy para español."""
    print("Instalando modelo de spaCy para español...")
    
    try:
        # Intentar descargar el modelo
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_sm"])
        print("✅ Modelo es_core_news_sm instalado exitosamente")
        
        # Verificar la instalación
        import spacy
        nlp = spacy.load("es_core_news_sm")
        print(f"✅ Modelo verificado: {nlp.meta['name']} v{nlp.meta['version']}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando el modelo: {e}")
        print("\nPuede instalarlo manualmente con:")
        print("  python -m spacy download es_core_news_sm")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error verificando el modelo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_spacy_model() 