#!/usr/bin/env python3
"""
TEST VERSO SOLUCIÓN FINAL
=========================

Verificar que el perfil verso corregido funciona correctamente
con el PDF de Neruda usando el VerseSegmenter tradicional.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
    
    def test_verso_solution():
        """Probar el perfil verso corregido con PDF de Neruda"""
        
        # Archivo de prueba (ajustar la ruta según sea necesario)
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            print("⚠️ Por favor ajustar la ruta del archivo en el script")
            return False
        
        print("🔍 VERIFICANDO PERFIL VERSO CORREGIDO")
        print("=" * 50)
        
        # Crear manager
        manager = ProfileManager()
        
        # Verificar que el perfil verso esté disponible
        profiles = {p['name']: p for p in manager.list_profiles()}
        if 'verso' not in profiles:
            print("❌ Perfil 'verso' no encontrado")
            return False
        
        # Mostrar configuración del perfil
        verso_profile = manager.get_profile('verso')
        print(f"📋 Perfil verso cargado:")
        print(f"   - Segmentador: {verso_profile.get('segmenter')}")
        print(f"   - Pre-procesador: {verso_profile.get('pre_processor')}")
        print(f"   - Configuración: {verso_profile.get('segmenter_config', {})}")
        print()
        
        # Verificar que el segmentador se puede crear
        segmenter = manager.create_segmenter('verso')
        if not segmenter:
            print("❌ No se pudo crear el segmentador 'verse'")
            return False
        
        print(f"✅ Segmentador creado: {type(segmenter).__name__}")
        print()
        
        # Procesar archivo
        print(f"📄 Procesando: {os.path.basename(test_file)}")
        print("⏳ Esto puede tomar unos momentos...")
        
        try:
            results = manager.process_file(
                file_path=test_file,
                profile_name='verso',
                language_override='es',
                confidence_threshold=0.3
            )
            
            # Desempaquetar resultados
            processed_items, segmenter_stats, document_metadata = results
            
            print()
            print("🎭 RESULTADOS DEL PROCESAMIENTO")
            print("=" * 40)
            print(f"📊 Segmentos encontrados: {len(processed_items)}")
            
            # Mostrar estadísticas del segmentador
            if segmenter_stats:
                print(f"📈 Estadísticas del segmentador:")
                for key, value in segmenter_stats.items():
                    print(f"   - {key}: {value}")
            
            # Mostrar información de los primeros segmentos
            if processed_items:
                print()
                print("🔍 PRIMEROS SEGMENTOS DETECTADOS:")
                for i, item in enumerate(processed_items[:3]):
                    print(f"\n--- Segmento {i+1} ---")
                    print(f"Tipo: {item.tipo_segmento}")
                    print(f"Longitud: {item.longitud_caracteres_segmento} caracteres")
                    if hasattr(item, 'texto_segmento'):
                        preview = item.texto_segmento[:100]
                        print(f"Preview: {preview}{'...' if len(item.texto_segmento) > 100 else ''}")
                
                print(f"\n✅ ¡ÉXITO! Se encontraron {len(processed_items)} segmentos")
                return True
            else:
                print("❌ No se encontraron segmentos")
                
                # Información de debug
                if document_metadata.get('error'):
                    print(f"❌ Error: {document_metadata['error']}")
                
                return False
                
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        print("🧪 TEST VERSO SOLUCIÓN FINAL")
        print("=" * 50)
        
        success = test_verso_solution()
        
        print()
        print("=" * 50)
        if success:
            print("🎉 ¡PRUEBA EXITOSA! El perfil verso está funcionando correctamente.")
        else:
            print("❌ PRUEBA FALLIDA. Revisar configuración.")
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 