"""
Implementación de PackageManager para Homebrew brew - PRD §RT-5
"""
import shutil
import json
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class BrewManager(PackageManager):
    """Gestor de paquetes Homebrew para macOS y Linux (brew)"""

    @property
    def name(self) -> str:
        return "brew"

    def verify_availability(self) -> bool:
        """Verifica si brew está disponible en el sistema"""
        return shutil.which("brew") is not None

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete brew o cask está instalado"""
        if not self.verify_availability():
            return False
        code, _, _ = run_command(["brew", "list", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un paquete brew"""
        if not self.verify_availability():
            return None
        code, stdout, _ = run_command(["brew", "info", "--json=v2", package_name])
        if code != 0 or not stdout:
            return None
        try:
            data = json.loads(stdout)
            formulae = data.get("formulae", [])
            if formulae:
                installed_info = formulae[0].get("installed", [])
                if installed_info:
                    return installed_info[0].get("version")
            casks = data.get("casks", [])
            if casks:
                return casks[0].get("version")
        except Exception:
            pass
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete brew de forma idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Paquete brew '{package.name}' ya está instalado.")
            return True

        cmd = ["brew", "install", package.name]

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando '{package.name}' vía Homebrew...")
        code, stdout, stderr = run_command(cmd, timeout=900)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía brew. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Lista todos los paquetes y casks instalados por Homebrew"""
        if not self.verify_availability():
            return []
        code, stdout, _ = run_command(["brew", "info", "--json=v2", "--installed"])
        if code != 0 or not stdout:
            return []
        try:
            data = json.loads(stdout)
            packages = []
            for f in data.get("formulae", []):
                installed_info = f.get("installed", [])
                ver = installed_info[0].get("version", "latest") if installed_info else "latest"
                packages.append(Package(
                    name=f["name"],
                    manager="brew",
                    version=ver,
                    description=f.get("desc", "Fórmula de Brew")
                ))
            for c in data.get("casks", []):
                packages.append(Package(
                    name=c["token"],
                    manager="brew",
                    version=c.get("version", "latest"),
                    description=c.get("desc", "Cask de Brew")
                ))
            return packages
        except Exception as e:
            logger.error(f"Error al parsear brew info json: {str(e)}")
            return []
