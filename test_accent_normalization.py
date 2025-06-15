#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unicodedata
from dataset.processing.contextual_author_detection import ContextualAuthorDetector
from dataset.processing.enhanced_contextual_author_detection import EnhancedContextualAuthorDetector, DocumentContext

def test_accent_normalization():
    """Test accent normalization in author detection"""
    print("=== PRUEBA DE NORMALIZACIÓN DE ACENTOS ===\n")
    
    # Crear detector base (donde está el fix)
    base_detector = ContextualAuthorDetector(config={'debug': True, 'strict_mode': False})
    
    # Crear detector mejorado
    enhanced_detector = EnhancedContextualAuthorDetector(config={'debug': True, 'strict_mode': False})
    
    # Probar normalización de acentos
    def normalize_accents(text):
        """Normaliza acentos para comparación"""
        return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    
    # Casos de prueba
    test_cases = [
        ("Ruben Dario", "Rubén Darío"),
        ("ruben dario", "rubén darío"),
        ("Pablo Neruda", "Pablo Neruda"),
        ("Garcia Lorca", "García Lorca"),
    ]
    
    print("1. Prueba de normalización de acentos:")
    for name_without, name_with in test_cases:
        normalized_without = normalize_accents(name_without.lower())
        normalized_with = normalize_accents(name_with.lower())
        match = normalized_without == normalized_with
        print(f"   '{name_without}' vs '{name_with}': {match}")
        print(f"      Normalizado: '{normalized_without}' vs '{normalized_with}'")
    
    print("\n2. Prueba de detección de autor conocido (detector base):")
    # Verificar si "Rubén Darío" está en la lista
    is_known_with_accents = base_detector._is_known_author("Rubén Darío")
    is_known_without_accents = base_detector._is_known_author("Ruben Dario")
    
    print(f"   'Rubén Darío' (con acentos): {is_known_with_accents}")
    print(f"   'Ruben Dario' (sin acentos): {is_known_without_accents}")
    
    print("\n3. Prueba de detección de autor conocido (detector mejorado):")
    # Verificar si "Rubén Darío" está en la lista
    is_known_with_accents_enh = enhanced_detector._is_known_author("Rubén Darío")
    is_known_without_accents_enh = enhanced_detector._is_known_author("Ruben Dario")
    
    print(f"   'Rubén Darío' (con acentos): {is_known_with_accents_enh}")
    print(f"   'Ruben Dario' (sin acentos): {is_known_without_accents_enh}")
    
    print("\n4. Prueba de extracción del contexto del documento:")
    doc_context = DocumentContext(
        title="Dario, Ruben - Antologia",
        filename="Dario, Ruben - Antologia.pdf"
    )
    
    extracted_author = enhanced_detector.extract_author_from_document_context(doc_context)
    print(f"   Autor extraído del título: '{extracted_author}'")
    
    if extracted_author:
        is_extracted_known_base = base_detector._is_known_author(extracted_author)
        is_extracted_known_enh = enhanced_detector._is_known_author(extracted_author)
        print(f"   ¿Es autor conocido? (base): {is_extracted_known_base}")
        print(f"   ¿Es autor conocido? (mejorado): {is_extracted_known_enh}")
    
    print("\n5. Verificando lista de autores conocidos:")
    if hasattr(base_detector, 'known_authors') and base_detector.known_authors:
        print(f"   Total autores conocidos: {len(base_detector.known_authors)}")
        # Buscar variaciones de Rubén Darío
        ruben_variants = [author for author in base_detector.known_authors if 'ruben' in author or 'rubén' in author]
        print(f"   Variantes de Rubén encontradas: {ruben_variants}")
    else:
        print("   ❌ No se cargaron autores conocidos")

if __name__ == "__main__":
    test_accent_normalization() 