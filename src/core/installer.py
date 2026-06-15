"""
Orquestador de instalación e informes - PRD §RF-2
"""
import time
from typing import List, Dict, Tuple, Optional
from src.models.package import Package, DotFile
from src.core.dependency_resolver import DependencyResolver
from src.core.dotfile_manager import DotfileManager
from src.managers.base import PackageManager
from src.managers.winget import WingetManager
from src.managers.pip import PipManager
from src.managers.npm import NpmManager
from src.managers.apt import AptManager
from src.managers.brew import BrewManager
from src.managers.flatpak import FlatpakManager
from src.managers.snap import SnapManager
from src.utils.shell import run_command
from src.utils.logger import logger

class InstallationReport:
    """Reporte del proceso de instalación final - PRD §RF-2"""
    
    def __init__(self, total: int = 0):
        self.total = total
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.failed_packages: List[Tuple[str, str]] = []
        self.start_time = time.time()
        self.end_time = 0.0

    def add_success(self):
        self.successful += 1

    def add_failure(self, name: str, error: str):
        self.failed += 1
        self.failed_packages.append((name, error))

    def add_skip(self):
        self.skipped += 1

    def finish(self):
        self.end_time = time.time()

    def elapsed_time_str(self) -> str:
        elapsed = (self.end_time or time.time()) - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes} minutos {seconds} segundos"

    def summary(self) -> str:
        time_str = self.elapsed_time_str()
        summary_lines = [
            "\n" + "═" * 40,
            "            RESUMEN DE RESTAURACIÓN",
            "═" * 40,
            f"Paquetes totales: {self.total}",
            f"Instalados con éxito: {self.successful} ✓",
            f"Fallidos: {self.failed} ✗",
            f"Omitidos/No disponibles: {self.skipped} ⏭️",
            f"Tiempo transcurrido: {time_str}"
        ]
        if self.failed_packages:
            summary_lines.append("\nDetalle de fallos:")
            for name, error in self.failed_packages:
                summary_lines.append(f"  - {name}: {error}")
        summary_lines.append("═" * 40)
        return "\n".join(summary_lines)


class InstallationOrchestrator:
    """Coordina la restauración idempotente y ordenada de un PC - PRD §RF-2"""

    def __init__(self, manifest_dir: str = "."):
        self.resolver = DependencyResolver()
        self.dotfile_mgr = DotfileManager(manifest_dir)
        
        # Mapeo de gestores de paquetes disponibles
        self.managers: Dict[str, PackageManager] = {
            "winget": WingetManager(),
            "pip": PipManager(),
            "npm": NpmManager(),
            "apt": AptManager(),
            "brew": BrewManager(),
            "flatpak": FlatpakManager(),
            "snap": SnapManager()
        }

    def get_manager(self, name: str) -> Optional[PackageManager]:
        """Obtiene el gestor de paquetes por su clave identificadora"""
        return self.managers.get(name.lower())

    def install_packages(
        self, 
        packages: List[Package], 
        dry_run: bool = False,
        skip_tier: Optional[int] = None,
        only_tier: Optional[int] = None
    ) -> InstallationReport:
        """
        Instala de forma secuencial y ordenada los paquetes del manifiesto.
        """
        # Filtrar paquetes por Tiers de prioridad
        filtered_packages = []
        for pkg in packages:
            if skip_tier is not None and pkg.tier >= skip_tier:
                continue
            if only_tier is not None and pkg.tier != only_tier:
                continue
            filtered_packages.append(pkg)

        # Resolver dependencias mediante Topological Sort
        try:
            sorted_pkgs = self.resolver.topological_sort(filtered_packages)
        except ValueError as e:
            logger.error(f"Error resolviendo orden de dependencias: {e}")
            raise

        # Cargar caché de paquetes instalados localmente para evitar múltiples llamadas en bucle
        local_installed_map = {}
        managers_to_check = {pkg.manager for pkg in sorted_pkgs}
        for name in managers_to_check:
            mgr = self.get_manager(name)
            if mgr and mgr.verify_availability():
                try:
                    logger.info(f"Cargando caché de paquetes instalados para '{name}'...")
                    for p in mgr.get_all_installed():
                        local_installed_map[f"{p.manager}:{p.name}"] = p.version
                except Exception as e:
                    logger.warning(f"No se pudo cargar la caché de '{name}': {e}")

        report = InstallationReport(total=len(sorted_pkgs))
        
        for idx, pkg in enumerate(sorted_pkgs, 1):
            mgr = self.get_manager(pkg.manager)
            if not mgr:
                err_msg = f"Gestor de paquetes '{pkg.manager}' no soportado."
                logger.error(f"[{idx}/{len(sorted_pkgs)}] ✗ {pkg.name}: {err_msg}")
                report.add_failure(pkg.name, err_msg)
                continue
                
            if not mgr.verify_availability():
                err_msg = f"Gestor '{pkg.manager}' no está disponible en este SO."
                logger.warning(f"[{idx}/{len(sorted_pkgs)}] ⏭️  Saltando '{pkg.name}' ({pkg.manager}): {err_msg}")
                report.add_skip()
                continue

            # Verificar estado instalado (Idempotencia)
            key = f"{pkg.manager}:{pkg.name}"
            already_installed = key in local_installed_map

            if already_installed:
                logger.info(f"[{idx}/{len(sorted_pkgs)}] ✓ Ya instalado: {pkg.name} ({pkg.manager})")
                report.add_success()
                continue

            # Si es winget y no tiene origen remoto, no podemos instalarlo remótamente
            if pkg.manager == "winget" and (pkg.repository == "local" or not pkg.repository):
                logger.warning(f"[{idx}/{len(sorted_pkgs)}] ⚠️  Saltando '{pkg.name}' ({pkg.manager}): Aplicación local sin origen remoto. Debe instalarse de forma manual.")
                report.add_skip()
                continue

            if dry_run:
                logger.info(f"[{idx}/{len(sorted_pkgs)}] ⏳ [DRY-RUN] Se instalaría: {pkg.name} ({pkg.manager}) [Tier {pkg.tier}]")
                report.add_success()
                continue
                
            logger.info(f"[{idx}/{len(sorted_pkgs)}] ⏳ Instalando: {pkg.name} ({pkg.manager})...")
            
            success = False
            error_msg = ""
            try:
                success = mgr.install(pkg, dry_run=False)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Excepción al instalar '{pkg.name}': {e}")

            if success:
                logger.info(f"[{idx}/{len(sorted_pkgs)}] ✓ Instalado con éxito: {pkg.name}")
                local_installed_map[key] = pkg.version
                # Ejecutar hooks post-instalación
                if pkg.post_install:
                    logger.info(f"  Ejecutando post_install para '{pkg.name}'...")
                    for hook in pkg.post_install:
                        logger.info(f"    $ {hook}")
                        # Permitimos shell=True para hooks personalizados
                        code, stdout, stderr = run_command(hook, shell=True)
                        if code != 0:
                            logger.warning(f"    ⚠️  El hook devolvió código de salida {code}: {stderr.strip()}")
                report.add_success()
            else:
                report.add_failure(pkg.name, error_msg or "La instalación falló")

        report.finish()
        return report

    def apply_dotfiles(self, dotfiles: List[DotFile], backup: bool = True, force: bool = False) -> bool:
        """Aplica los dotfiles de configuración"""
        logger.info("\nAplicando archivos de configuración (dotfiles)...")
        all_success = True
        for df in dotfiles:
            if df.is_secret:
                logger.warning(f"⚠️  Saltando dotfile secreto: {df.source_path}")
                continue
            try:
                success = self.dotfile_mgr.apply_dotfile(df, backup=backup, force=force)
                if not success:
                    all_success = False
            except PermissionError as e:
                logger.error(f"❌ ALERTA CRÍTICA DE SEGURIDAD: {e}")
                logger.error("Se aborta la restauración para proteger la integridad del sistema.")
                return False
        return all_success
