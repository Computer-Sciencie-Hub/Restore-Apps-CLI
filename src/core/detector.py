"""
Detector del sistema y escáner de paquetes instalados - PRD §RF-1
"""
import platform
import os
import datetime
import hashlib
from typing import List
from src.models.system_info import SystemInfo
from src.models.package import Package, DotFile
from src.managers.base import PackageManager
from src.managers.winget import WingetManager
from src.managers.pip import PipManager
from src.managers.npm import NpmManager
from src.managers.apt import AptManager
from src.managers.brew import BrewManager
from src.managers.flatpak import FlatpakManager
from src.managers.snap import SnapManager
from src.utils.crypto import check_value_for_secrets
from src.utils.logger import logger

class SystemDetector:
    """Detecta la configuración del sistema operativo y paquetes instalados - PRD §RF-1"""

    def __init__(self):
        # Registrar todos los gestores compatibles
        self.managers: List[PackageManager] = [
            WingetManager(),
            PipManager(),
            NpmManager(),
            AptManager(),
            BrewManager(),
            FlatpakManager(),
            SnapManager()
        ]

    def get_system_info(self) -> SystemInfo:
        """Obtiene la información detallada del sistema actual"""
        os_name = platform.system().lower()
        if os_name == "linux":
            try:
                with open("/etc/os-release") as f:
                    content = f.read()
                    if "ubuntu" in content.lower():
                        os_type = "ubuntu"
                    elif "debian" in content.lower():
                        os_type = "debian"
                    elif "fedora" in content.lower():
                        os_type = "fedora"
                    elif "arch" in content.lower():
                        os_type = "arch"
                    else:
                        os_type = "linux"
            except Exception:
                os_type = "linux"
        else:
            os_type = os_name

        return SystemInfo(
            os=os_type,
            os_version=platform.release(),
            arch=platform.machine(),
            hostname=platform.node() or "unknown",
            user=os.environ.get("USER") or os.environ.get("USERNAME") or "root",
            timestamp=datetime.datetime.now().isoformat() + "Z"
        )

    def get_available_managers(self) -> List[PackageManager]:
        """Retorna únicamente los gestores de paquetes disponibles en este SO"""
        available = []
        for mgr in self.managers:
            try:
                if mgr.verify_availability():
                    available.append(mgr)
            except Exception as e:
                logger.warning(f"Error verificando disponibilidad de {mgr.name}: {e}")
        return available

    def scan_all_managers(self) -> List[Package]:
        """Escanea todos los gestores disponibles y retorna la lista agregada de paquetes"""
        packages = []
        available = self.get_available_managers()
        for mgr in available:
            logger.info(f"Escaneando paquetes instalados con '{mgr.name}'...")
            try:
                pkg_list = mgr.get_all_installed()
                packages.extend(pkg_list)
                logger.info(f"  ✓ Encontrados {len(pkg_list)} paquetes en '{mgr.name}'.")
            except Exception as e:
                logger.error(f"Error escaneando gestor '{mgr.name}': {e}")
        return packages

    def scan_dotfiles(self, paths: List[str] = None) -> List[DotFile]:
        """
        Escanea archivos de configuración en el directorio del usuario.
        Evita añadir archivos marcados como secretos.
        """
        if not paths:
            # Manifiesto por defecto de dotfiles comunes
            paths = [".bashrc", ".gitconfig", ".profile", ".config/code/settings.json"]
            
        dotfiles = []
        home_dir = os.path.expanduser("~")
        
        for p in paths:
            full_path = os.path.join(home_dir, p)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Verificar secreto en el nombre de la ruta
                is_secret = len(check_value_for_secrets(p)) > 0
                if any(ext in p.lower() for ext in [".env", ".pem", ".key", "id_rsa", "id_ed25519", "credentials"]):
                    is_secret = True
                
                # Calcular checksum
                hasher = hashlib.sha256()
                try:
                    with open(full_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    checksum = hasher.hexdigest()
                    
                    dotfiles.append(DotFile(
                        source_path=p,
                        destination_path=f"~/{p}",
                        is_secret=is_secret,
                        create_symlink=False,
                        checksum=checksum
                    ))
                except Exception as e:
                    logger.warning(f"No se pudo escanear el dotfile '{p}': {e}")
                    
        return dotfiles
