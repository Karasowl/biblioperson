"""
Gestor de Meilisearch para Biblioperson.

Este módulo maneja la detección, descarga e inicio automático de Meilisearch
de forma transparente para el usuario.
"""

import os
import sys
import platform
import subprocess
import logging
import requests
import zipfile
import tarfile
import time
import json
import psutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import socket
import urllib.request
import shutil

logger = logging.getLogger(__name__)


class MeilisearchManager:
    """Gestiona la instalación y ejecución de Meilisearch."""
    
    def __init__(self, data_dir: str = "data.ms/meilisearch", 
                 port: int = 7700, 
                 master_key: Optional[str] = None):
        """
        Inicializa el gestor de Meilisearch.
        
        Args:
            data_dir: Directorio para datos de Meilisearch
            port: Puerto para Meilisearch (default: 7700)
            master_key: Clave maestra para Meilisearch (opcional)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.port = port
        self.master_key = master_key or os.getenv("MEILISEARCH_MASTER_KEY", "")
        
        # Directorio para binarios
        self.bin_dir = Path("data.ms/bin")
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Determinar sistema operativo y arquitectura
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        
        # Proceso de Meilisearch
        self.process = None
        
        # URL base para descargas
        self.download_base_url = "https://github.com/meilisearch/meilisearch/releases/latest/download"
        
    def get_binary_name(self) -> str:
        """Obtiene el nombre del binario según el sistema operativo."""
        if self.system == "windows":
            return "meilisearch.exe"
        return "meilisearch"
    
    def get_download_filename(self) -> str:
        """Obtiene el nombre del archivo a descargar según el sistema."""
        if self.system == "windows":
            if "64" in self.machine or "amd64" in self.machine:
                return "meilisearch-windows-amd64.exe"
            else:
                return "meilisearch-windows-386.exe"
        elif self.system == "darwin":  # macOS
            if "arm" in self.machine:
                return "meilisearch-macos-apple-silicon"
            else:
                return "meilisearch-macos-amd64"
        else:  # Linux
            if "aarch64" in self.machine or "arm64" in self.machine:
                return "meilisearch-linux-aarch64"
            elif "armv" in self.machine:
                return "meilisearch-linux-armv7"
            else:
                return "meilisearch-linux-amd64"
    
    def is_port_in_use(self, port: int) -> bool:
        """Verifica si un puerto está en uso."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return False
            except:
                return True
    
    def find_meilisearch_process(self) -> Optional[psutil.Process]:
        """Encuentra un proceso de Meilisearch en ejecución."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Verificar por nombre
                if 'meilisearch' in proc.info['name'].lower():
                    return proc
                    
                # Verificar por línea de comandos
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('meilisearch' in str(arg).lower() for arg in cmdline):
                    return proc
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def is_meilisearch_running(self) -> bool:
        """Verifica si Meilisearch está corriendo."""
        # Verificar si el puerto está en uso
        if not self.is_port_in_use(self.port):
            return False
            
        # Verificar si responde a peticiones HTTP
        try:
            response = requests.get(f"http://localhost:{self.port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_binary_path(self) -> Path:
        """Obtiene la ruta al binario de Meilisearch."""
        return self.bin_dir / self.get_binary_name()
    
    def is_installed(self) -> bool:
        """Verifica si Meilisearch está instalado."""
        binary_path = self.get_binary_path()
        return binary_path.exists() and binary_path.is_file()
    
    def download_meilisearch(self) -> bool:
        """Descarga Meilisearch si no está instalado."""
        if self.is_installed():
            logger.info("Meilisearch ya está instalado")
            return True
            
        logger.info("Descargando Meilisearch...")
        
        try:
            # Construir URL de descarga
            download_filename = self.get_download_filename()
            download_url = f"{self.download_base_url}/{download_filename}"
            
            logger.info(f"Descargando desde: {download_url}")
            
            # Descargar archivo
            temp_file = self.bin_dir / f"meilisearch_temp_{int(time.time())}"
            
            # Usar urllib para mostrar progreso
            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(downloaded * 100 / total_size, 100)
                logger.debug(f"Descarga: {percent:.1f}%")
            
            urllib.request.urlretrieve(download_url, temp_file, reporthook=download_progress)
            
            # Renombrar al nombre final
            final_path = self.get_binary_path()
            shutil.move(str(temp_file), str(final_path))
            
            # Hacer ejecutable en sistemas Unix
            if self.system != "windows":
                os.chmod(final_path, 0o755)
            
            logger.info("✅ Meilisearch descargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error descargando Meilisearch: {str(e)}")
            # Limpiar archivo temporal si existe
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def start_meilisearch(self, force_restart: bool = False) -> bool:
        """
        Inicia Meilisearch si no está corriendo.
        
        Args:
            force_restart: Si forzar reinicio aunque esté corriendo
            
        Returns:
            True si se inició correctamente
        """
        # Verificar si ya está corriendo
        if self.is_meilisearch_running():
            if not force_restart:
                logger.info("Meilisearch ya está corriendo")
                return True
            else:
                logger.info("Reiniciando Meilisearch...")
                self.stop_meilisearch()
                time.sleep(2)
        
        # Descargar si no está instalado
        if not self.is_installed():
            if not self.download_meilisearch():
                return False
        
        # Preparar comando
        binary_path = self.get_binary_path()
        cmd = [
            str(binary_path),
            "--db-path", str(self.data_dir),
            "--http-addr", f"127.0.0.1:{self.port}",
            "--no-analytics"
        ]
        
        if self.master_key:
            cmd.extend(["--master-key", self.master_key])
        
        # Configurar entorno
        env = os.environ.copy()
        env["MEILI_NO_ANALYTICS"] = "true"
        
        try:
            # Iniciar proceso en background sin ventana
            if self.system == "windows":
                # En Windows, usar CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # En Unix, usar subprocess normal
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    preexec_fn=os.setsid if self.system != "windows" else None
                )
            
            # Esperar a que inicie
            logger.info("Esperando a que Meilisearch inicie...")
            for i in range(30):  # Esperar hasta 30 segundos
                time.sleep(1)
                if self.is_meilisearch_running():
                    logger.info("✅ Meilisearch iniciado correctamente")
                    
                    # Crear índice si no existe
                    self.ensure_index_exists()
                    
                    return True
                    
                # Verificar si el proceso murió
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    logger.error(f"Meilisearch terminó inesperadamente")
                    logger.error(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
                    logger.error(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
                    return False
            
            logger.error("Timeout esperando a que Meilisearch inicie")
            return False
            
        except Exception as e:
            logger.error(f"Error iniciando Meilisearch: {str(e)}")
            return False
    
    def stop_meilisearch(self):
        """Detiene Meilisearch si está corriendo."""
        # Intentar detener nuestro proceso
        if self.process and self.process.poll() is None:
            logger.info("Deteniendo proceso de Meilisearch...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
        
        # Buscar y detener cualquier proceso de Meilisearch
        proc = self.find_meilisearch_process()
        if proc:
            logger.info(f"Deteniendo proceso de Meilisearch (PID: {proc.pid})...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()
            except psutil.NoSuchProcess:
                pass
    
    def ensure_index_exists(self, index_name: str = "biblioperson"):
        """Asegura que el índice existe en Meilisearch."""
        try:
            headers = {}
            if self.master_key:
                headers['Authorization'] = f'Bearer {self.master_key}'
            
            # Verificar si el índice existe
            response = requests.get(
                f"http://localhost:{self.port}/indexes/{index_name}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 404:
                # Crear índice
                logger.info(f"Creando índice '{index_name}'...")
                response = requests.post(
                    f"http://localhost:{self.port}/indexes",
                    json={
                        "uid": index_name,
                        "primaryKey": "id"
                    },
                    headers=headers
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"✅ Índice '{index_name}' creado")
                    
                    # Configurar ajustes del índice
                    self.configure_index_settings(index_name)
                else:
                    logger.warning(f"Error creando índice: {response.text}")
            
        except Exception as e:
            logger.warning(f"Error verificando/creando índice: {str(e)}")
    
    def configure_index_settings(self, index_name: str = "biblioperson"):
        """Configura los ajustes del índice para búsqueda en español."""
        try:
            headers = {}
            if self.master_key:
                headers['Authorization'] = f'Bearer {self.master_key}'
            
            # Configurar campos buscables
            settings = {
                "searchableAttributes": [
                    "text",
                    "document_title", 
                    "document_author"
                ],
                "filterableAttributes": [
                    "document_id",
                    "document_author",
                    "segment_type",
                    "language",
                    "original_page"
                ],
                "sortableAttributes": [
                    "segment_order",
                    "original_page"
                ],
                "displayedAttributes": [
                    "id",
                    "document_id",
                    "document_title",
                    "document_author",
                    "text",
                    "segment_type",
                    "segment_order",
                    "original_page",
                    "language"
                ],
                "rankingRules": [
                    "words",
                    "typo",
                    "proximity",
                    "attribute",
                    "sort",
                    "exactness"
                ]
            }
            
            response = requests.patch(
                f"http://localhost:{self.port}/indexes/{index_name}/settings",
                json=settings,
                headers=headers
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Configuración del índice actualizada")
            else:
                logger.warning(f"Error configurando índice: {response.text}")
                
        except Exception as e:
            logger.warning(f"Error configurando índice: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de Meilisearch."""
        try:
            headers = {}
            if self.master_key:
                headers['Authorization'] = f'Bearer {self.master_key}'
            
            response = requests.get(
                f"http://localhost:{self.port}/stats",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    def __enter__(self):
        """Context manager: inicia Meilisearch al entrar."""
        self.start_meilisearch()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: detiene Meilisearch al salir."""
        # No detener automáticamente, dejar corriendo
        pass


# Singleton global
_meilisearch_manager: Optional[MeilisearchManager] = None


def get_meilisearch_manager() -> MeilisearchManager:
    """Obtiene la instancia singleton del gestor de Meilisearch."""
    global _meilisearch_manager
    if _meilisearch_manager is None:
        _meilisearch_manager = MeilisearchManager()
    return _meilisearch_manager


def ensure_meilisearch_running() -> bool:
    """
    Asegura que Meilisearch esté corriendo.
    
    Returns:
        True si Meilisearch está corriendo o se inició correctamente
    """
    manager = get_meilisearch_manager()
    return manager.start_meilisearch()


if __name__ == "__main__":
    # Prueba del gestor
    logging.basicConfig(level=logging.INFO)
    
    manager = MeilisearchManager()
    
    print(f"Sistema: {manager.system}")
    print(f"Arquitectura: {manager.machine}")
    print(f"Binario: {manager.get_binary_name()}")
    print(f"Archivo descarga: {manager.get_download_filename()}")
    
    if manager.is_meilisearch_running():
        print("✅ Meilisearch ya está corriendo")
    else:
        print("🔄 Iniciando Meilisearch...")
        if manager.start_meilisearch():
            print("✅ Meilisearch iniciado correctamente")
            
            # Obtener estadísticas
            stats = manager.get_stats()
            print(f"📊 Estadísticas: {json.dumps(stats, indent=2)}")
        else:
            print("❌ Error iniciando Meilisearch") 