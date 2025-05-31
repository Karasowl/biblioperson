#!/usr/bin/env python3
"""
Test del nuevo detector inteligente de títulos para ebooks.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_title_detection():
    """Test específico del detector de títulos"""
    
    print("🧪 TESTING DETECTOR INTELIGENTE DE TÍTULOS")
    print("=" * 60)
    
    try:
        # Importar módulos
        from dataset.scripts.process_file import _process_single_file, ProcessingStats
        from dataset.processing.profile_manager import ProfileManager
        from pathlib import Path
        
        print("✅ Importaciones exitosas")
        
        # Configurar paths
        input_path = Path(r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf")
        output_path = Path(r"C:\Users\adven\Downloads\New folder (13)\test_ebook_detection.ndjson")
        
        # Asegurar que el directorio de salida existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear args con perfil EBOOK
        class Args:
            def __init__(self):
                self.profile = 'ebook'  # 🎯 USAR NUEVO PERFIL EBOOK
                self.language_override = 'es'
                self.author_override = None
                self.verbose = True
                self.encoding = 'utf-8'
                self.output_format = 'json'
                self.output = str(output_path)
                self.input_path = str(input_path)
                self.force_type = None
                self.confidence_threshold = 0.5
                self.parallel = False
                self.max_workers = None
        
        args = Args()
        stats = ProcessingStats()
        profile_manager = ProfileManager()
        
        print(f"🎯 Usando perfil: {args.profile}")
        print(f"📁 Archivo de entrada: {input_path}")
        print(f"💾 Archivo de salida: {output_path}")
        
        # Procesar archivo
        print("\n🔄 INICIANDO PROCESAMIENTO CON DETECCIÓN DE TÍTULOS...")
        success = _process_single_file(
            input_path, 
            output_path, 
            args, 
            stats, 
            profile_manager
        )
        
        if success:
            print(f"\n✅ ¡PROCESAMIENTO EXITOSO!")
            print(f"📄 Archivo generado: {output_path}")
            
            # Verificar si el archivo fue creado
            if output_path.exists():
                print(f"✅ Archivo confirmado: {output_path.stat().st_size} bytes")
                
                # Buscar títulos específicos en el resultado
                print(f"\n🔍 BUSCANDO TÍTULOS DETECTADOS...")
                
                # Leer y analizar primeras líneas
                with open(output_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]  # Primeras 20 líneas
                
                title_count = 0
                for i, line in enumerate(lines):
                    try:
                        import json
                        data = json.loads(line)
                        segment_type = data.get('tipo_segmento', 'unknown')
                        text = data.get('texto_segmento', '')[:100]
                        
                        if 'title_level' in segment_type:
                            title_count += 1
                            print(f"🎯 {segment_type}: {text}...")
                        elif 'introducción' in text.lower():
                            print(f"📋 {segment_type}: {text}...")
                            
                    except json.JSONDecodeError:
                        continue
                
                print(f"\n📊 RESULTADO: {title_count} títulos detectados en las primeras 20 líneas")
                
                # Buscar específicamente "Introducción"
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'introducción' in content.lower():
                        print("✅ Se encontró 'Introducción' en el archivo")
                        # Buscar la línea específica
                        for line in content.split('\n'):
                            if 'introducción' in line.lower() and 'populistas' in line.lower():
                                try:
                                    data = json.loads(line)
                                    tipo = data.get('tipo_segmento', 'unknown')
                                    print(f"🎯 'Introducción | ¿Son todos populistas?' detectado como: {tipo}")
                                    break
                                except:
                                    pass
            else:
                print(f"❌ Error: El archivo no fue creado")
                
        else:
            print(f"❌ Error en el procesamiento")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_title_detection() 