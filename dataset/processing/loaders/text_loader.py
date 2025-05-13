from datetime import datetime
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader

class TextLoader(BaseLoader):
    """Loader para archivos de texto plano (.txt)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de texto plano.
        
        Args:
            file_path: Ruta al archivo de texto
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación del archivo
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        
    def _extract_date_from_filename(self) -> Optional[str]:
        """Intenta extraer una fecha del nombre del archivo."""
        # Patrones comunes de fecha en nombres de archivo
        patterns = [
            r'(\d{4})[_-](\d{1,2})[_-](\d{1,2})',  # YYYY-MM-DD o YYYY_MM_DD
            r'(\d{1,2})[_-](\d{1,2})[_-](\d{4})',  # DD-MM-YYYY o DD_MM_YYYY
            r'(\d{4})(\d{2})(\d{2})'              # YYYYMMDD
        ]
        
        filename = self.file_path.stem
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                # Asegurar que sea una fecha válida
                try:
                    if len(match.groups()) == 3:
                        if pattern == patterns[0]:  # YYYY-MM-DD
                            year, month, day = match.groups()
                        elif pattern == patterns[1]:  # DD-MM-YYYY
                            day, month, year = match.groups()
                        else:  # YYYYMMDD
                            year, month, day = match.groups()
                            
                        # Asegurar que los valores son numéricos
                        year, month, day = int(year), int(month), int(day)
                        
                        # Validar rango
                        if 1900 <= year <= datetime.now().year and 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
                    
        return None
        
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo de texto.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados como bloques de texto individuales
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        
        with self.file_path.open('r', encoding=self.encoding) as f:
            try:
                contenido = f.read()
                lineas = contenido.split('\n')
                
                # Detectar título si la primera línea está separada del resto
                titulo = None
                inicio = 0
                
                if len(lineas) > 1 and not lineas[0].strip().endswith('.') and len(lineas[0].strip()) < 100:
                    if lineas[1].strip() == '':  # Título seguido de línea en blanco
                        titulo = lineas[0].strip()
                        inicio = 2  # Empezar desde la tercera línea (después del título y línea en blanco)
                
                # Primero, pasamos el título si existe
                if titulo:
                    yield {
                        'text': titulo,
                        'is_heading': True,
                        'heading_level': 1,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha
                    }
                
                # Luego, pasamos cada línea de texto como un bloque
                for i, linea in enumerate(lineas[inicio:], inicio):
                    yield {
                        'text': linea,
                        'is_heading': False,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha
                    }
                    
            except UnicodeDecodeError as e:
                print(f"Error de codificación en {self.file_path}: {e}. Intenta con otra codificación.")
                raise
    
    def _parece_poema(self, lineas: list) -> bool:
        """
        Detecta si el texto parece tener formato de poema basado en características heurísticas.
        
        Args:
            lineas: Lista de líneas del texto
            
        Returns:
            True si parece un poema, False si parece prosa
        """
        if not lineas:
            return False
            
        # Filtrar líneas vacías
        no_vacias = [l for l in lineas if l.strip()]
        if len(no_vacias) < 4:  # Muy poco texto para determinar
            return False
            
        # Características que indican poesía
        lineas_cortas = 0
        lineas_terminadas_sin_punto = 0
        estrofas = 1
        lineas_vacias_consecutivas = 0
        
        for i, linea in enumerate(lineas):
            if not linea.strip():
                lineas_vacias_consecutivas += 1
                if lineas_vacias_consecutivas >= 2:
                    estrofas += 1
                    lineas_vacias_consecutivas = 0
            else:
                lineas_vacias_consecutivas = 0
                
                # Contar líneas cortas (típicas de poesía)
                if len(linea.strip()) < 60:
                    lineas_cortas += 1
                    
                # Contar líneas que no terminan en punto (típico de versos)
                if linea.strip() and not linea.strip().endswith('.') and not linea.strip().endswith('?') and not linea.strip().endswith('!'):
                    lineas_terminadas_sin_punto += 1
        
        # Calcular porcentajes
        porcentaje_cortas = lineas_cortas / len(no_vacias) if no_vacias else 0
        porcentaje_sin_punto = lineas_terminadas_sin_punto / len(no_vacias) if no_vacias else 0
        
        # Puntaje de poema
        puntaje = 0
        if porcentaje_cortas > 0.7:  # Mayoría de líneas cortas
            puntaje += 0.5
        if porcentaje_sin_punto > 0.6:  # Mayoría no terminan en punto
            puntaje += 0.3
        if estrofas > 1:  # Tiene múltiples estrofas
            puntaje += 0.2
            
        return puntaje > 0.6  # Umbral para considerar como poema 