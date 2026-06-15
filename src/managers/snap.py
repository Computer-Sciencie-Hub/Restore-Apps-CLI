"""
Implementación de PackageManager para Linux snap - PRD §RT-5
"""
import shutil
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class SnapManager(PackageManager):
    """Gestor de paquetes Snap para Linux"""

    @property
    def name(self) -> str:
        return "snap"

    def verify_availability(self) -> bool:
        """Verifica si snap está disponible en el sistema"""
        return shutil.which("snap") is not None

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete snap está instalado"""
        if not self.verify_availability():
            return False
        code, _, _ = run_command(["snap", "list", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un snap"""
        if not self.verify_availability():
            return None
        code, stdout, _ = run_command(["snap", "list", package_name])
        if code != 0:
            return None
        lines = stdout.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 2:
                return parts[1]
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un snap de manera idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Snap '{package.name}' ya está instalado.")
            return True

        cmd = ["sudo", "snap", "install", package.name]
        # Algunos paquetes comunes de desarrollo requieren el flag --classic
        if package.name in {"code", "pycharm-community", "intellij-idea-community", "gitkraken", "node"}:
            cmd.append("--classic")

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando '{package.name}' vía snap...")
        code, stdout, stderr = run_command(cmd, timeout=600)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía snap. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Lista todos los paquetes instalados por snap en el sistema"""
        if not self.verify_availability():
            return []
        code, stdout, _ = run_command(["snap", "list"])
        if code != 0:
            return []
        packages = []
        lines = stdout.splitlines()
        if len(lines) > 1:
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    packages.append(Package(
                        name=parts[0],
                        manager="snap",
                        version=parts[1],
                        description="Paquete snap"
                    ))
        return packages
