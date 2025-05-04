#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para probar la generación de embeddings
"""

from embedding_service import EmbeddingService

def probar_embeddings():
    print("Probando servicio de embeddings...")
    
    # Inicializar servicio
    service = EmbeddingService()
    
    # Probar con varios textos
    textos_prueba = [
        "amor y fe",
        "La importancia de la fe en tiempos difíciles",
        "Un texto largo sobre diversos temas filosóficos y existenciales que debería funcionar sin problemas",
        "a",  # Texto muy corto
        "",   # Texto vacío
        "amor",
        "fe",
        "cristianismo"
    ]
    
    print("\nProbando textos:")
    print("----------------")
    
    for texto in textos_prueba:
        print(f"\nProbando texto: '{texto}'")
        embedding = service.generar_embedding(texto)
        
        if embedding:
            print(f"✓ Embedding generado correctamente - Dimensión: {len(embedding)}")
            # Mostrar primeros 5 valores para verificar
            print(f"Primeros valores: {embedding[:5]}")
        else:
            print(f"✗ No se pudo generar embedding")
    
    print("\nPrueba completada")

if __name__ == "__main__":
    probar_embeddings() 