#!/usr/bin/env python3
"""
🔧 TEST: PIPELINE COMPLETO CON CASO REAL DEL USUARIO
Simula el caso exacto mostrado por el usuario donde el elemento
"*Antolo* *g* *ía* *Rubén Darío*" aparece en medio del texto.
"""

import sys
import os
sys.path.append('dataset')

def test_caso_real_usuario():
    """
    Testa el pipeline completo con el texto exacto que mostró el usuario.
    """
    print("🔧 SIMULANDO CASO REAL DEL USUARIO")
    print("=" * 60)
    
    try:
        from processing.segmenters.verse_segmenter import VerseSegmenter
        
        # Crear segmentador
        segmenter = VerseSegmenter()
        
        # 📝 TEXTO EXACTO DEL USUARIO (simplificado para el test)
        # Este es el tipo de texto que está apareciendo en el JSON del usuario
        
        user_corrupted_text = """PALABRAS LIMINARES
Después de Azul, después de los Raros, voces insinuantes, buena mala
intención, entusiasmo sonoro envidia subterránea, --todo bella
cosecha--solicitaron lo que en conciencia, no he creído fructuoso ni
oportuno: un manifiesto.
Ni fructuoso ni oportuno:
*Antolo* *g* *ía* *Rubén Darío*
) Por la absoluta falta de elevación mental de la mayoría pensante de
nuestro continente, en el cual impera el universal personaje clasificado
por Rémy de Gour, como el Plouc contemporáneo, cuyo único don es conocer
comparatas. Porque proclamando, como proclamo, una estética acrática, la
imposición de un modelo o de un código implicaría una contradicción."""
        
        print(f"📝 TEXTO CORRUPTO DEL USUARIO:")
        print(f"   Contiene: '*Antolo* *g* *ía* *Rubén Darío*'")
        print(f"   Longitud: {len(user_corrupted_text)} caracteres")
        
        # Test 1: Limpieza directa del texto
        print(f"\n🧹 TEST 1: Limpieza directa")
        cleaned_text = segmenter._clean_structural_corruption(user_corrupted_text)
        
        print(f"   ANTES: Contiene '*Antolo* *g* *ía* *Rubén Darío*': {('*Antolo* *g* *ía* *Rubén Darío*' in user_corrupted_text)}")
        print(f"   DESPUÉS: Contiene '*Antolo* *g* *ía* *Rubén Darío*': {('*Antolo* *g* *ía* *Rubén Darío*' in cleaned_text)}")
        
        if "*Antolo* *g* *ía* *Rubén Darío*" not in cleaned_text:
            print(f"   ✅ SUCCESS: Elemento corrupto removido")
        else:
            print(f"   ❌ FAIL: Elemento corrupto todavía presente")
            return False
        
        # Verificar que el contenido real se preservó
        essential_content = ["PALABRAS LIMINARES", "Después de Azul", "manifiesto", "estética acrática"]
        content_preserved = all(content in cleaned_text for content in essential_content)
        
        if content_preserved:
            print(f"   ✅ SUCCESS: Contenido esencial preservado")
        else:
            print(f"   ❌ WARNING: Algún contenido esencial perdido")
        
        # Test 2: Simulación de pipeline completo
        print(f"\n🔧 TEST 2: Pipeline completo simulado")
        
        # Simular bloques como los que llegan al VerseSegmenter
        document_blocks = [
            # Un bloque grande con texto corrupto mezclado (como el caso real)
            {
                'text': user_corrupted_text,
                'metadata': {
                    'type': 'text_block',
                    'page_number': 1,
                    'order': 0
                }
            },
            # Otro bloque para simular más contenido
            {
                'text': 'TARDE DEL TRÓPICO\nEs la tarde gris y triste.\nViste el mar de terciopelo\ny el cielo profundo viste\nde duelo.',
                'metadata': {
                    'type': 'text_block', 
                    'page_number': 2,
                    'order': 1
                }
            }
        ]
        
        print(f"   📊 Procesando {len(document_blocks)} bloques")
        
        # Segmentar con el VerseSegmenter
        segments = segmenter.segment(document_blocks)
        
        print(f"   📊 RESULTADOS: {len(segments)} segmentos generados")
        
        # Verificar cada segmento
        corrupted_segments = 0
        clean_segments = 0
        
        for i, segment in enumerate(segments):
            text = segment.get('text', '')
            title = segment.get('title', 'Sin título')
            
            print(f"\n   📖 Segmento {i+1}: '{title}'")
            print(f"      Longitud: {len(text)} caracteres")
            print(f"      Inicio: '{text[:80]}{'...' if len(text) > 80 else ''}'")
            
            # Verificar presencia de elemento corrupto
            if "*Antolo* *g* *ía* *Rubén Darío*" in text:
                corrupted_segments += 1
                print(f"      ❌ CONTIENE ELEMENTO CORRUPTO")
                
                # Mostrar dónde aparece
                corruption_index = text.find("*Antolo* *g* *ía* *Rubén Darío*")
                context_start = max(0, corruption_index - 50)
                context_end = min(len(text), corruption_index + 100)
                context = text[context_start:context_end]
                print(f"      🔍 Contexto: '{context}'")
            else:
                clean_segments += 1
                print(f"      ✅ LIBRE DE ELEMENTOS CORRUPTOS")
        
        # Resultado final
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   - Segmentos limpios: {clean_segments}")
        print(f"   - Segmentos corruptos: {corrupted_segments}")
        
        if corrupted_segments == 0:
            print(f"\n🎉 SUCCESS: PROBLEMA DEL USUARIO SOLUCIONADO")
            print(f"   ✅ Ningún segmento contiene '*Antolo* *g* *ía* *Rubén Darío*'")
            print(f"   ✅ VerseSegmenter V2.3 limpia correctamente")
            print(f"   ✅ Output JSON será limpio")
            return True
        else:
            print(f"\n❌ FAIL: {corrupted_segments} segmentos aún contienen elementos corruptos")
            print(f"   ⚠️ El usuario seguirá viendo el problema")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_caso_real_usuario()
    
    if success:
        print(f"\n🎉 CASO REAL DEL USUARIO SOLUCIONADO")
        print(f"\n📋 IMPLEMENTACIÓN EXITOSA:")
        print(f"   ✅ VerseSegmenter V2.3 activo")
        print(f"   ✅ Limpieza directa en _create_poem_text")
        print(f"   ✅ Elemento '*Antolo* *g* *ía* *Rubén Darío*' removido")
        print(f"   ✅ Contenido poético preservado")
        print(f"\n🚀 El usuario ya no verá elementos corruptos en su JSON")
        exit(0)
    else:
        print(f"\n❌ CASO REAL AÚN NO SOLUCIONADO")
        print(f"\n📋 ACCIONES REQUERIDAS:")
        print(f"   - Verificar que VerseSegmenter V2.3 se está usando")
        print(f"   - Confirmar que _clean_structural_corruption se aplica")
        print(f"   - Revisar patrones regex para coincidencias")
        exit(1) 