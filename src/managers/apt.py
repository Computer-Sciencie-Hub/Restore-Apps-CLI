"""
Implementación de PackageManager para Debian/Ubuntu apt - PRD §RT-5
"""
import shutil
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class AptManager(PackageManager):
    """Gestor de paquetes para Debian/Ubuntu (apt)"""

    @property
    def name(self) -> str:
        return "apt"

    def verify_availability(self) -> bool:
        """Verifica si apt-get y dpkg están disponibles en el sistema"""
        return shutil.which("apt-get") is not None and shutil.which("dpkg") is not None

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete apt está instalado"""
        if not self.verify_availability():
            return False
        code, _, _ = run_command(["dpkg", "-s", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un paquete apt"""
        if not self.verify_availability():
            return None
        code, stdout, _ = run_command(["dpkg-query", "-W", "-f=${Version}", package_name])
        if code == 0:
            return stdout.strip()
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete apt de forma idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Paquete apt '{package.name}' ya está instalado.")
            return True

        cmd = ["sudo", "apt-get", "install", "-y"]
        if package.version and package.version != "latest":
            cmd.append(f"{package.name}={package.version}")
        else:
            cmd.append(package.name)

        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True

        logger.info(f"Instalando '{package.name}' vía apt...")
        code, stdout, stderr = run_command(cmd, timeout=600)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía apt. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def get_all_installed(self) -> List[Package]:
        """Obtiene la lista de todos los paquetes instalados por dpkg en el sistema"""
        if not self.verify_availability():
            return []
        code, stdout, _ = run_command(["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Description}\n"])
        if code != 0:
            return []
            
        packages = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                desc = parts[2] if len(parts) > 2 else ""
                packages.append(Package(
                    name=parts[0],
                    manager="apt",
                    version=parts[1],
                    description=desc.strip()[:100]
                ))
        return packages
