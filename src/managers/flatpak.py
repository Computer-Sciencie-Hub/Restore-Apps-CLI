"""
Implementación de PackageManager para Linux flatpak - PRD §RT-5
"""
import shutil
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class FlatpakManager(PackageManager):
    """Gestor de paquetes Flatpak universal para Linux"""

    @property
    def name(self) -> str:
        return "flatpak"

    def verify_availability(self) -> bool:
        """Verifica si flatpak está disponible en el sistema"""
        return shutil.which("flatpak") is not None

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete flatpak está instalado"""
        if not self.verify_availability():
            return False
        code, _, _ = run_command(["flatpak", "info", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un flatpak"""
        if not self.verify_availability():
            return None
        code, stdout, _ = run_command(["flatpak", "info", "--show-version", package_name])
        if code == 0:
            return stdout.strip()
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete flatpak de forma idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Flatpak '{package.name}' ya está instalado.")
            return True

        # Asumimos flathub como repositorio principal por defecto
        cmd = ["flatpak", "install", "-y", "flathub", package.name]

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando '{package.name}' vía flatpak...")
        code, stdout, stderr = run_command(cmd, timeout=600)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía flatpak. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Lista todos los paquetes flatpak instalados en el sistema"""
        if not self.verify_availability():
            return []
        code, stdout, _ = run_command(["flatpak", "list", "--columns=application,version,name"])
        if code != 0:
            return []
            
        packages = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                packages.append(Package(
                    name=parts[0],
                    manager="flatpak",
                    version=parts[1] if parts[1] else "latest",
                    description=parts[2] if len(parts) > 2 else "Aplicación Flatpak"
                ))
        return packages
