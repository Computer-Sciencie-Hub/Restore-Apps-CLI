"""
Implementación de PackageManager para Node.js npm global - PRD §RT-5
"""
import shutil
import json
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class NpmManager(PackageManager):
    """Gestor de paquetes para Node.js (npm global)"""

    @property
    def name(self) -> str:
        return "npm"

    def verify_availability(self) -> bool:
        """Verifica si npm está disponible en la PATH"""
        if shutil.which("npm") is not None:
            return True
        code, _, _ = run_command(["npm", "--version"])
        return code == 0

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete npm está instalado globalmente"""
        code, _, _ = run_command(["npm", "list", "-g", "--depth=0", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un paquete npm global"""
        code, stdout, _ = run_command(["npm", "list", "-g", "--depth=0", "--json"])
        if not stdout:
            return None
        try:
            data = json.loads(stdout)
            deps = data.get("dependencies", {})
            if package_name in deps:
                return deps[package_name].get("version")
        except Exception:
            pass
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete npm global de manera idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Paquete npm global '{package.name}' ya está instalado.")
            return True

        cmd = ["npm", "install", "-g"]
        if package.version and package.version != "latest":
            cmd.append(f"{package.name}@{package.version}")
        else:
            cmd.append(package.name)

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando globalmente '{package.name}' vía npm...")
        code, stdout, stderr = run_command(cmd, timeout=300)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía npm. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Lista todos los paquetes globales instalados por npm"""
        code, stdout, _ = run_command(["npm", "list", "-g", "--depth=0", "--json"])
        if not stdout:
            return []
        try:
            data = json.loads(stdout)
            deps = data.get("dependencies", {})
            packages = []
            for name, info in deps.items():
                packages.append(Package(
                    name=name,
                    manager="npm",
                    version=info.get("version", "unknown"),
                    description="Paquete global de Node.js"
                ))
            return packages
        except Exception as e:
            logger.error(f"Error al parsear npm list json: {str(e)}")
            return []
