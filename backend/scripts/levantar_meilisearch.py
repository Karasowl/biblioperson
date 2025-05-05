import subprocess
import os
import sys
from pathlib import Path

# Ruta al ejecutable de Meilisearch (ajusta si cambias el nombre o carpeta)
MEILI_PATH = Path(__file__).parent.parent / 'meilisearch' / 'meilisearch-windows-amd64.exe'

if not MEILI_PATH.exists():
    print(f"No se encontró el ejecutable de Meilisearch en: {MEILI_PATH}")
    sys.exit(1)

# Opcional: puedes agregar argumentos como --master-key o --db-path si lo necesitas
cmd = [str(MEILI_PATH)]

print(f"Levantando Meilisearch desde: {MEILI_PATH}")
subprocess.Popen(cmd, cwd=MEILI_PATH.parent)
print("Meilisearch iniciado en segundo plano. Puedes acceder a http://127.0.0.1:7700")
