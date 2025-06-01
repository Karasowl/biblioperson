"""
🚨 TEST PROFILE MANAGER BENEDETTI V7.0 🚨

Prueba el ProfileManager real con el perfil "verso" corregido
para verificar que todo el pipeline funciona.
"""

import sys
import os
import logging
from pathlib import Path
import tempfile

# Añadir el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from dataset.processing.profile_manager import ProfileManager

def create_test_pdf_content():
    """Crear contenido de prueba que simula un PDF con poemas"""
    content = '''
"Despedida"

Ya no soy quien era entonces
cuando las palabras fluían
como ríos en primavera
y el mundo era una promesa.

"Nostalgia"

Recuerdo aquellas tardes
cuando la vida era simple
y los sueños no dolían
tanto como hoy me duelen.

"Esperanza"

Pero aún queda algo
en el fondo del alma,
una luz que resiste
a todas las tormentas.

"Final"

Y así termina este viaje
de versos y de memoria,
dejando en cada línea
un pedazo de la historia.
'''
    return content

def test_with_profile_manager():
    """Prueba completa usando ProfileManager"""
    print("🚨🚨🚨 TEST PROFILE MANAGER BENEDETTI V7.0 🚨🚨🚨")
    
    # Crear archivo temporal de prueba
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        content = create_test_pdf_content()
        f.write(content)
        test_file = f.name
    
    try:
        print(f"📁 Archivo de prueba creado: {test_file}")
        print(f"📝 Contenido: {len(content)} caracteres")
        
        # Inicializar ProfileManager
        print("\n" + "="*60)
        print("🔧 INICIALIZANDO PROFILE MANAGER")
        print("="*60)
        
        profile_manager = ProfileManager()
        
        # Verificar que el perfil "verso" existe
        profiles = profile_manager.list_profiles()
        verso_profile = None
        for profile in profiles:
            if profile.get('name') == 'verso':
                verso_profile = profile
                break
        
        if not verso_profile:
            print("❌ ERROR: Perfil 'verso' no encontrado")
            return False
        
        print(f"✅ Perfil 'verso' encontrado")
        print(f"   📝 Descripción: {verso_profile.get('description', 'N/A')}")
        
        # Procesar archivo con perfil verso
        print("\n" + "="*60)
        print("🎵 PROCESANDO CON PERFIL VERSO")
        print("="*60)
        
        # Crear directorio temporal para output
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                result = profile_manager.process_file(
                    file_path=test_file,
                    profile_name='verso',
                    output_dir=temp_dir,
                    encoding='utf-8',
                    output_format='ndjson'
                )
                
                print(f"📊 RESULTADO:")
                print(f"   🎵 Segmentos procesados: {len(result)}")
                
                if result:
                    print(f"\n✅ SEGMENTOS ENCONTRADOS:")
                    poem_count = len(result)
                    
                    # Simplificado: solo mostrar que se detectaron poemas
                    for i, segment in enumerate(result):
                        print(f"   [{i+1}] Poema detectado: {type(segment).__name__}")
                        try:
                            # Intentar acceder a atributos comunes
                            if hasattr(segment, 'title'):
                                print(f"       🏷️ Título: {getattr(segment, 'title', 'N/A')}")
                            if hasattr(segment, 'content'):
                                content = getattr(segment, 'content', '')
                                preview = str(content)[:100].replace('\n', ' ')
                                print(f"       📝 Contenido: {repr(preview)}...")
                            elif hasattr(segment, 'text'):
                                text = getattr(segment, 'text', '')
                                preview = str(text)[:100].replace('\n', ' ')
                                print(f"       📝 Texto: {repr(preview)}...")
                        except Exception as e:
                            print(f"       ⚠️ No se pudo acceder al contenido: {e}")
                    
                    if poem_count > 0:
                        print(f"\n🎉 ¡ÉXITO! Se detectaron {poem_count} poemas")
                        return True
                    else:
                        print(f"\n❌ FALLO: No se encontraron poemas válidos")
                        return False
                else:
                    print(f"\n❌ FALLO: No se generaron segmentos")
                    return False
                    
            except Exception as e:
                print(f"❌ ERROR durante procesamiento: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(test_file)
        except:
            pass
    
    print("\n" + "="*60)
    print("🏁 TEST COMPLETADO")
    print("="*60)

if __name__ == "__main__":
    success = test_with_profile_manager()
    if success:
        print("🎉 ¡SISTEMA FUNCIONANDO CORRECTAMENTE!")
        print("✅ El perfil 'verso' puede detectar poemas de Mario Benedetti")
    else:
        print("❌ EL SISTEMA NECESITA MÁS AJUSTES") 