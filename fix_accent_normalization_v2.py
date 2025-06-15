#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def fix_accent_normalization_v2():
    """Fix the accent normalization issue in contextual_author_detection.py"""
    
    file_path = "dataset/processing/contextual_author_detection.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The method seems to have been corrupted. Let's find and replace the entire method
    # Look for the method starting around line 773
    
    # Find the start of the method
    method_start_pattern = r'    def _is_known_author\(self, name: str\) -> bool:\s*\n\s*"""Verifica si un nombre está en la lista de autores conocidos"""'
    
    # Find all occurrences
    matches = list(re.finditer(method_start_pattern, content))
    
    if len(matches) >= 2:
        # Get the second occurrence (in ContextualAuthorDetector class)
        second_match = matches[1]
        start_pos = second_match.start()
        
        # Find the end of the method by looking for the next method definition
        remaining_content = content[start_pos:]
        
        # Find where this method ends (next method or function definition)
        end_pattern = r'\n\n# Función de conveniencia'
        end_match = re.search(end_pattern, remaining_content)
        
        if end_match:
            end_pos = start_pos + end_match.start()
            
            # Extract the corrupted method
            old_method = content[start_pos:end_pos]
            
            # Define the correct method
            new_method = '''    def _is_known_author(self, name: str) -> bool:
        """Verifica si un nombre está en la lista de autores conocidos"""
        if not self.known_authors:
            return False
        
        name_lower = name.lower().strip()
        
        # Normalizar acentos para comparación
        def normalize_accents(text):
            """Normaliza acentos para comparación"""
            import unicodedata
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
            
            # Replace the method
            new_content = content[:start_pos] + new_method + content[end_pos:]
            
            # Write the file back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Fixed accent normalization in _is_known_author method (v2)")
            print(f"   Replaced corrupted method at position {start_pos}")
            print(f"   Old method length: {len(old_method)} chars")
            print(f"   New method length: {len(new_method)} chars")
            
        else:
            print("❌ Could not find the end of the method")
    else:
        print("❌ Could not find the _is_known_author method to fix")
        print(f"   Found {len(matches)} occurrences")

if __name__ == "__main__":
    fix_accent_normalization_v2() 