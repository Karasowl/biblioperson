#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import unicodedata

def fix_accent_normalization():
    """Fix the accent normalization issue in contextual_author_detection.py"""
    
    file_path = "dataset/processing/contextual_author_detection.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _is_known_author method in the ContextualAuthorDetector class (the second occurrence)
    # Look for the method that starts around line 728
    old_method = '''    def _is_known_author(self, name: str) -> bool:
        """Verifica si un nombre está en la lista de autores conocidos"""
        if not self.known_authors:
            return False
        
        name_lower = name.lower().strip()
        
        # Búsqueda exacta
        if name_lower in self.known_authors:
            return True
        
        # Búsqueda por partes (nombre y apellido por separado)
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            # Buscar combinaciones comunes
            full_name_variants = [
                ' '.join(name_parts),
                ' '.join(name_parts[:2]),  # Solo primeros dos nombres
                f"{name_parts[-1]}, {' '.join(name_parts[:-1])}",  # Apellido, Nombre
            ]
            
            for variant in full_name_variants:
                if variant in self.known_authors:
                    return True
        
        return False'''
    
    new_method = '''    def _is_known_author(self, name: str) -> bool:
        """Verifica si un nombre está en la lista de autores conocidos"""
        if not self.known_authors:
            return False
        
        name_lower = name.lower().strip()
        
        # Normalizar acentos para comparación
        def normalize_accents(text):
            """Normaliza acentos para comparación"""
            return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
        
        name_normalized = normalize_accents(name_lower)
        
        # Búsqueda exacta (con y sin acentos)
        if name_lower in self.known_authors or name_normalized in self.known_authors:
            return True
        
        # También buscar en la lista normalizada
        for known_author in self.known_authors:
            if normalize_accents(known_author) == name_normalized:
                return True
        
        # Búsqueda por partes (nombre y apellido por separado)
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            # Buscar combinaciones comunes
            full_name_variants = [
                ' '.join(name_parts),
                ' '.join(name_parts[:2]),  # Solo primeros dos nombres
                f"{name_parts[-1]}, {' '.join(name_parts[:-1])}",  # Apellido, Nombre
            ]
            
            for variant in full_name_variants:
                if variant in self.known_authors:
                    return True
                
                # También buscar variante normalizada
                variant_normalized = normalize_accents(variant)
                if variant_normalized in self.known_authors:
                    return True
                
                # Buscar en la lista normalizada
                for known_author in self.known_authors:
                    if normalize_accents(known_author) == variant_normalized:
                        return True
        
        return False'''
    
    # Find the last occurrence of the method (in ContextualAuthorDetector class)
    # We need to be careful to replace the right one
    
    # Split content by the method definition to find both occurrences
    method_pattern = r'    def _is_known_author\(self, name: str\) -> bool:'
    matches = list(re.finditer(method_pattern, content))
    
    if len(matches) >= 2:
        # Get the second occurrence (in ContextualAuthorDetector class)
        second_match = matches[1]
        start_pos = second_match.start()
        
        # Find the end of the method by looking for the next method or class definition
        # Look for the next line that starts with 4 spaces followed by 'def ' or end of file
        remaining_content = content[start_pos:]
        
        # Find the end of this method
        lines = remaining_content.split('\n')
        method_lines = []
        in_method = True
        
        for i, line in enumerate(lines):
            if i == 0:  # First line is the method definition
                method_lines.append(line)
                continue
            
            # If we find a line that starts with 4 spaces and 'def ' or 'class ', we've reached the next method/class
            if line.strip() and not line.startswith('        ') and not line.startswith('    def _is_known_author'):
                if line.startswith('# ') or line.startswith('def ') or line.startswith('class '):
                    break
            
            method_lines.append(line)
            
            # Stop when we reach the return False line
            if line.strip() == 'return False':
                break
        
        old_method_actual = '\n'.join(method_lines)
        
        # Replace the method
        new_content = content.replace(old_method_actual, new_method, 1)
        
        # Write the file back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed accent normalization in _is_known_author method")
        print(f"   Replaced method starting at position {start_pos}")
        print(f"   Method had {len(method_lines)} lines")
        
    else:
        print("❌ Could not find the _is_known_author method to fix")
        print(f"   Found {len(matches)} occurrences")

if __name__ == "__main__":
    fix_accent_normalization() 