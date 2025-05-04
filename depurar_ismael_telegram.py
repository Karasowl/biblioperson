import json

input_path = "backend/contenido/redes_sociales/Telegram/debates_ismael_filtrado.ndjson"
output_path = "backend/contenido/redes_sociales/Telegram/debates_ismael_SOLO_ISMAEL.ndjson"

with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
    for line in infile:
        try:
            obj = json.loads(line)
            if obj.get("author") == "Ismael":
                outfile.write(line)
        except Exception:
            continue  # Si hay una línea corrupta, la ignora

print("¡Archivo depurado! Solo quedan los mensajes de Ismael.") 