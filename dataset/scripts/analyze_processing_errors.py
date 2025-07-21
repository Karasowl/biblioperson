#!/usr/bin/env python3
"""
Script para analizar errores de procesamiento y generar un resumen detallado.

Este script analiza el archivo processing_errors.log y otros logs para identificar
los tipos de errores más comunes y proporcionar estadísticas útiles.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import argparse
from typing import Dict, List, Tuple, Any

# Función utilitaria para manejo seguro de emojis
def safe_emoji_print(text: str, fallback_text: str = None) -> None:
    """Imprime texto con emojis de forma segura, usando fallback si hay problemas de encoding."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Si hay problema con emojis, usar texto alternativo
        if fallback_text:
            print(fallback_text)
        else:
            # Remover emojis y usar solo texto ASCII
            import re
            ascii_text = re.sub(r'[^\x00-\x7F]+', '[EMOJI]', text)
            print(ascii_text)


class ProcessingErrorAnalyzer:
    """Analizador de errores de procesamiento."""
    
    def __init__(self, log_file_path="processing_errors.log"):
        self.log_file_path = Path(log_file_path)
        self.errors = []
        self.error_stats = defaultdict(int)
        self.file_errors = defaultdict(list)
        self.error_types = Counter()
        
    def analyze_log_file(self):
        """Analiza el archivo de log de errores."""
        if not self.log_file_path.exists():
            safe_emoji_print(f"❌ Archivo de log no encontrado: {self.log_file_path}", f"[ERROR] Archivo de log no encontrado: {self.log_file_path}")
            return
            
        safe_emoji_print(f"📊 Analizando errores en: {self.log_file_path}", f"[INFO] Analizando errores en: {self.log_file_path}")
        
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Dividir por entradas de error (cada una empieza con timestamp)
        error_entries = re.split(r'\n(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
        
        for entry in error_entries:
            if entry.strip():
                self._parse_error_entry(entry.strip())
                
        self._categorize_errors()
        
    def _parse_error_entry(self, entry):
        """Parsea una entrada de error individual."""
        lines = entry.split('\n')
        if not lines:
            return
            
        # Extraer timestamp y mensaje principal
        first_line = lines[0]
        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', first_line)
        
        if not timestamp_match:
            return
            
        timestamp = timestamp_match.group(1)
        
        # Extraer archivo afectado
        file_match = re.search(r'para (?:archivo )?([^:]+?)(?:\s*:|$)', first_line)
        affected_file = file_match.group(1) if file_match else "Desconocido"
        
        # Extraer tipo de error
        error_type = self._extract_error_type(entry)
        
        # Extraer mensaje de error
        error_message = self._extract_error_message(entry)
        
        error_info = {
            'timestamp': timestamp,
            'affected_file': affected_file,
            'error_type': error_type,
            'error_message': error_message,
            'full_entry': entry
        }
        
        self.errors.append(error_info)
        self.file_errors[affected_file].append(error_info)
        
    def _extract_error_type(self, entry):
        """Extrae el tipo de error de la entrada."""
        # Buscar tipos de error comunes
        if 'NameError' in entry:
            return 'NameError'
        elif 'AttributeError' in entry:
            return 'AttributeError'
        elif 'TypeError' in entry:
            return 'TypeError'
        elif 'FileNotFoundError' in entry:
            return 'FileNotFoundError'
        elif 'PDFLoader' in entry:
            return 'PDF Loader Error'
        elif 'loader' in entry.lower():
            return 'Loader Error'
        elif 'segmenter' in entry.lower():
            return 'Segmenter Error'
        else:
            return 'Unknown Error'
            
    def _extract_error_message(self, entry):
        """Extrae el mensaje de error principal."""
        lines = entry.split('\n')
        
        # Buscar líneas que contengan el error principal
        for line in lines:
            if any(error_type in line for error_type in ['Error', 'Exception', 'NameError', 'AttributeError', 'TypeError']):
                # Limpiar el mensaje
                message = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - [^-]+ - ERROR - ', '', line)
                return message.strip()
                
        return "Mensaje no identificado"
        
    def _categorize_errors(self):
        """Categoriza los errores por tipo."""
        for error in self.errors:
            self.error_types[error['error_type']] += 1
            
    def generate_report(self):
        """Genera un reporte detallado de errores."""
        print("\n" + "="*80)
        print("📋 REPORTE DE ANÁLISIS DE ERRORES DE PROCESAMIENTO")
        print("="*80)
        
        safe_emoji_print(f"\n📊 **ESTADÍSTICAS GENERALES**", f"\n[STATS] **ESTADÍSTICAS GENERALES**")
        print(f"   • Total de errores encontrados: {len(self.errors)}")
        print(f"   • Archivos afectados: {len(self.file_errors)}")
        print(f"   • Tipos de error únicos: {len(self.error_types)}")
        
        safe_emoji_print(f"\n🔍 **TIPOS DE ERROR MÁS COMUNES**", f"\n[ANALYSIS] **TIPOS DE ERROR MÁS COMUNES**")
        for error_type, count in self.error_types.most_common():
            percentage = (count / len(self.errors)) * 100
            print(f"   • {error_type}: {count} errores ({percentage:.1f}%)")
            
        safe_emoji_print(f"\n📁 **ARCHIVOS MÁS PROBLEMÁTICOS**", f"\n[FILES] **ARCHIVOS MÁS PROBLEMÁTICOS**")
        file_error_counts = {file: len(errors) for file, errors in self.file_errors.items()}
        sorted_files = sorted(file_error_counts.items(), key=lambda x: x[1], reverse=True)
        
        for file, count in sorted_files[:10]:  # Top 10
            print(f"   • {file}: {count} errores")
            
        safe_emoji_print(f"\n🔧 **ERRORES ESPECÍFICOS DETECTADOS**", f"\n[ERRORS] **ERRORES ESPECÍFICOS DETECTADOS**")
        
        # Agrupar errores similares
        error_patterns = defaultdict(list)
        for error in self.errors:
            # Crear una clave basada en el tipo y mensaje principal
            key = f"{error['error_type']}: {error['error_message'][:100]}"
            error_patterns[key].append(error)
            
        for pattern, errors in list(error_patterns.items())[:10]:  # Top 10 patrones
            print(f"\n   🚨 {pattern}")
            print(f"      Ocurrencias: {len(errors)}")
            if len(errors) <= 3:
                for error in errors:
                    print(f"      - Archivo: {error['affected_file']}")
            else:
                print(f"      - Archivos afectados: {len(set(e['affected_file'] for e in errors))}")
                
        print(f"\n💡 **RECOMENDACIONES**")
        self._generate_recommendations()
        
    def _generate_recommendations(self):
        """Genera recomendaciones basadas en los errores encontrados."""
        recommendations = []
        
        # Analizar tipos de error y generar recomendaciones
        if self.error_types.get('NameError', 0) > 0:
            recommendations.append("🔧 Corregir variables no definidas (NameError) - revisar pdf_loader.py")
            
        if self.error_types.get('PDF Loader Error', 0) > 0:
            recommendations.append("📄 Revisar y corregir el PDF Loader - problemas con metadatos")
            
        if self.error_types.get('AttributeError', 0) > 0:
            recommendations.append("🔍 Verificar métodos y atributos de objetos")
            
        if self.error_types.get('Loader Error', 0) > 0:
            recommendations.append("📂 Revisar compatibilidad de loaders con diferentes formatos de archivo")
            
        # Recomendaciones específicas basadas en archivos
        problematic_extensions = defaultdict(int)
        for file in self.file_errors.keys():
            if '.' in file:
                ext = Path(file).suffix.lower()
                problematic_extensions[ext] += 1
                
        if problematic_extensions.get('.pdf', 0) > 0:
            recommendations.append("📋 Priorizar corrección del PDF Loader")
            
        if problematic_extensions.get('.docx', 0) > 0:
            recommendations.append("📝 Revisar DOCX Loader")
            
        for rec in recommendations:
            print(f"   {rec}")
            
        if not recommendations:
            safe_emoji_print("   ✅ No se detectaron patrones específicos para recomendaciones", "   [OK] No se detectaron patrones específicos para recomendaciones")
            
    def save_detailed_report(self, output_file="error_analysis_report.json"):
        """Guarda un reporte detallado en formato JSON."""
        report_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_errors': len(self.errors),
            'affected_files_count': len(self.file_errors),
            'error_types': dict(self.error_types),
            'errors_by_file': {file: len(errors) for file, errors in self.file_errors.items()},
            'detailed_errors': self.errors
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        safe_emoji_print(f"\n💾 Reporte detallado guardado en: {output_file}", f"\n[SAVED] Reporte detallado guardado en: {output_file}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Analizar errores de procesamiento')
    parser.add_argument('--log-file', default='processing_errors.log', 
                       help='Archivo de log a analizar')
    parser.add_argument('--output', default='error_analysis_report.json',
                       help='Archivo de salida para reporte detallado')
    parser.add_argument('--verbose', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    analyzer = ProcessingErrorAnalyzer(args.log_file)
    analyzer.analyze_log_file()
    analyzer.generate_report()
    analyzer.save_detailed_report(args.output)


if __name__ == "__main__":
    main()