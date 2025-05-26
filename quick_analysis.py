#!/usr/bin/env python3
"""
Análisis rápido de archivos no soportados basado en logs de TSC
"""

def main():
    # Datos del resumen de logs
    total_archivos = 211
    exitosos = 94
    errores = 117
    
    print('🔍 ANÁLISIS DE ARCHIVOS NO SOPORTADOS DE TSC')
    print('=' * 60)
    print()
    print('📊 RESUMEN GENERAL:')
    print(f'   • Total de archivos encontrados: {total_archivos}')
    print(f'   • Total de archivos exitosos: {exitosos}')
    print(f'   • Total de archivos fallidos: {errores}')
    print(f'   • Tasa de éxito: {(exitosos/total_archivos)*100:.1f}%')
    print(f'   • Tasa de error: {(errores/total_archivos)*100:.1f}%')
    print()
    
    # Estimación basada en muestra de logs visible
    extensiones_estimadas = {
        '.docx': 25,    # Muchos documentos Word fallaron
        '.xlsx': 20,    # Hojas de cálculo Excel
        '.key': 8,      # Claves privadas
        '.cer': 6,      # Certificados
        '.req': 4,      # Requerimientos de certificados
        '.pfx': 2,      # Certificados empaquetados
        '.png': 4,      # Imágenes PNG
        '.jpg': 2,      # Imágenes JPG
        '.mp4': 3,      # Videos
        '.html': 4,     # Archivos web
        '.zip': 1,      # Archivos comprimidos
        '.ini': 1,      # Archivos de configuración
        '.sdg': 2,      # Archivos de firma digital
    }
    
    print('📋 CONTEO ESTIMADO POR EXTENSIÓN:')
    total_estimado = 0
    for ext, count in sorted(extensiones_estimadas.items(), key=lambda x: x[1], reverse=True):
        print(f'   {ext:8} → {count:3} archivos')
        total_estimado += count
    
    otros = errores - total_estimado
    if otros > 0:
        print(f'   {"Otros":8} → {otros:3} archivos')
    
    print(f'\nTotal estimado: {errores} archivos')
    
    print('\n📁 CATEGORÍAS PRINCIPALES:')
    
    categories = {
        "🔐 Certificados/Llaves": ['.key', '.cer', '.req', '.pfx', '.sdg'],
        "📊 Hojas de cálculo": ['.xlsx'],
        "📝 Documentos Word": ['.docx'],
        "🖼️ Imágenes": ['.png', '.jpg'],
        "🎥 Videos": ['.mp4'],
        "🌐 Archivos web": ['.html'],
        "🗜️ Archivos comprimidos": ['.zip'],
        "⚙️ Sistema/Config": ['.ini']
    }
    
    for categoria, extensiones in categories.items():
        total_categoria = sum(extensiones_estimadas.get(ext, 0) for ext in extensiones)
        if total_categoria > 0:
            print(f'\n   {categoria} ({total_categoria} archivos):')
            for ext in extensiones:
                count = extensiones_estimadas.get(ext, 0)
                if count > 0:
                    porcentaje = (count/errores)*100
                    print(f'      {ext:8} → {count:3} archivos ({porcentaje:.1f}% del total)')
    
    print(f'\n💡 PRINCIPALES PROBLEMAS IDENTIFICADOS:')
    print(f'   1. 📝 Documentos Word (.docx): ~25 archivos (~21% de errores)')
    print(f'      - Posible corrupción o formatos no estándar')
    print(f'      - Documentos con contraseña o protegidos')
    print(f'   2. 📊 Hojas Excel (.xlsx): ~20 archivos (~17% de errores)')
    print(f'      - Archivos binarios complejos')
    print(f'      - Hojas con macros o formatos especiales')
    print(f'   3. 🔐 Certificados/Llaves: ~22 archivos (~19% de errores)')
    print(f'      - Archivos binarios sin contenido de texto')
    print(f'      - No deberían procesarse como documentos')
    print(f'   4. 🖼️ Multimedia: ~9 archivos (~8% de errores)')
    print(f'      - Imágenes (.png, .jpg) y videos (.mp4)')
    print(f'      - Requieren OCR o transcripción')
    
    print(f'\n✅ RECOMENDACIONES:')
    print(f'   • Para .docx/.xlsx: Verificar integridad y agregar manejo de errores')
    print(f'   • Para certificados: Excluir del procesamiento o crear filtro')
    print(f'   • Para imágenes: Implementar OCR si contienen texto relevante')
    print(f'   • Para videos: Extraer subtítulos o transcripciones si es necesario')
    print(f'   • Para HTML: Agregar parser HTML básico')

if __name__ == "__main__":
    main() 