#!/usr/bin/env python3
"""
🔧 DEBUG: INVESTIGAR PROBLEMA DE EXPORTACIÓN
Debuggea paso a paso por qué la exportación no funciona.
"""

import os
import sys
import tempfile
from pathlib import Path

# Agregar path del dataset
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

def debug_export_issue():
    """
    Debuggea el problema de exportación paso a paso.
    """
    print("🔧 DEBUGGEANDO PROBLEMA DE EXPORTACIÓN")
    print("=" * 60)
    
    try:
        from processing.profile_manager import ProfileManager
        
        # Crear archivo de prueba
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("Poema 1\n\nEste es un verso\nEste es otro verso")
            temp_file_path = temp_file.name
        
        print(f"✅ Archivo de prueba creado: {temp_file_path}")
        
        # Crear directorio temporal para salida
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "debug_output.ndjson"
            print(f"✅ Archivo de salida objetivo: {output_file}")
            
            # Inicializar ProfileManager
            manager = ProfileManager()
            print("✅ ProfileManager inicializado")
            
            # STEP 1: Verificar que el archivo existe
            if not Path(temp_file_path).exists():
                print("❌ ERROR: Archivo de prueba no existe")
                return False
            else:
                print("✅ Archivo de prueba existe")
            
            # STEP 2: Llamar a process_file con debug
            print("\n🔍 LLAMANDO A process_file...")
            print(f"  - file_path: {temp_file_path}")
            print(f"  - profile_name: verso")
            print(f"  - output_file: {output_file}")
            print(f"  - output_format: ndjson")
            
            try:
                result = manager.process_file(
                    file_path=temp_file_path,
                    profile_name='verso',
                    output_file=str(output_file),
                    output_format='ndjson'
                )
                
                print(f"✅ process_file completado")
                print(f"  - Tipo de resultado: {type(result)}")
                print(f"  - Longitud del resultado: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                
                if isinstance(result, tuple) and len(result) >= 3:
                    segments, stats, metadata = result[:3]
                    print(f"  - Segmentos: {len(segments) if segments else 0}")
                    print(f"  - Stats: {stats}")
                    print(f"  - Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
                    if metadata:
                        print(f"  - Metadata error: {metadata.get('error', 'None')}")
                        print(f"  - Metadata warning: {metadata.get('warning', 'None')}")
                
            except Exception as e:
                print(f"❌ ERROR en process_file: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
            
            # STEP 3: Verificar si se creó el archivo de salida
            print(f"\n🔍 VERIFICANDO ARCHIVO DE SALIDA...")
            if output_file.exists():
                if output_file.is_file():
                    print(f"✅ Archivo creado correctamente: {output_file}")
                    
                    # Verificar contenido
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"  - Tamaño del archivo: {len(content)} caracteres")
                        print(f"  - Primeros 200 caracteres: {content[:200]}...")
                        
                        lines = content.strip().split('\n') if content.strip() else []
                        print(f"  - Número de líneas: {len(lines)}")
                        
                        if len(lines) > 0:
                            print("✅ Exportación exitosa")
                            return True
                        else:
                            print("❌ Archivo creado pero está vacío")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error leyendo archivo: {str(e)}")
                        return False
                        
                elif output_file.is_dir():
                    print(f"❌ ERROR: Se creó directorio en lugar de archivo: {output_file}")
                    return False
            else:
                print(f"❌ ERROR: No se creó archivo de salida: {output_file}")
                
                # Verificar si se creó algo similar
                parent_dir = output_file.parent
                print(f"🔍 Contenido del directorio padre: {list(parent_dir.iterdir())}")
                return False
                
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpiar
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

if __name__ == "__main__":
    success = debug_export_issue()
    if success:
        print(f"\n🎉 DEBUG COMPLETADO - EXPORTACIÓN FUNCIONA")
        exit(0)
    else:
        print(f"\n❌ DEBUG COMPLETADO - EXPORTACIÓN FALLA")
        exit(1) 