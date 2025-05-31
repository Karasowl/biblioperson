import json

def examinar_output():
    file_path = "C:/Users/adven/OneDrive/Escritorio/New folder (3)/output.ndjson"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total de líneas: {len(lines)}")
    
    for i, line in enumerate(lines[:5]):
        try:
            data = json.loads(line)
            content = data.get("content", "")
            print(f"\nSegmento {i+1}:")
            print(f"Tipo: {data.get('type', 'unknown')}")
            print(f"Content (primeros 200 chars): {content[:200]}")
            if len(content) > 200:
                print("...")
        except Exception as e:
            print(f"Error procesando línea {i+1}: {e}")

if __name__ == "__main__":
    examinar_output() 