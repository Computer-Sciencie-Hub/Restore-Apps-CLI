"""
Implementación de PackageManager para Python pip - PRD §RT-5
"""
import shutil
import json
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class PipManager(PackageManager):
    """Gestor de paquetes para Python (pip)"""

    @property
    def name(self) -> str:
        return "pip"

    def verify_availability(self) -> bool:
        """Verifica si pip está disponible en la PATH"""
        if shutil.which("pip") is not None:
            return True
        code, _, _ = run_command(["pip", "--version"])
        return code == 0

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete pip está instalado"""
        code, _, _ = run_command(["pip", "show", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un paquete pip"""
        code, stdout, _ = run_command(["pip", "show", package_name])
        if code != 0:
            return None
        for line in stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete pip de forma idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Paquete pip '{package.name}' ya está instalado.")
            return True

        cmd = ["pip", "install"]
        if package.version and package.version != "latest":
            cmd.append(f"{package.name}=={package.version}")
        else:
            cmd.append(package.name)

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando '{package.name}' vía pip...")
        code, stdout, stderr = run_command(cmd, timeout=300)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía pip. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Obtiene todos los paquetes instalados por pip en el entorno actual"""
        code, stdout, _ = run_command(["pip", "list", "--format=json"])
        if code != 0:
            return []
        try:
            items = json.loads(stdout)
            return [
                Package(
                    name=item["name"],
                    manager="pip",
                    version=item["version"],
                    description="Paquete de entorno Python"
                )
                for item in items
            ]
        except Exception as e:
            logger.error(f"Error al parsear pip list json: {str(e)}")
            return []
