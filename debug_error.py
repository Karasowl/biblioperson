import sys
sys.path.insert(0, '.')
from dataset.processing.profile_manager import ProfileManager

try:
    pm = ProfileManager()
    result = pm.process_file(
        'C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/escritos/Biblioteca virtual/¿Qué es el populismo_ - Jan-Werner Müller.pdf',
        'prosa',
        language_override='es'
    )
    print('SUCCESS')
except Exception as e:
    import traceback
    print('ERROR:', str(e))
    traceback.print_exc() 