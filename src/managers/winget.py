"""
Implementación de PackageManager para Windows winget - PRD §RT-5
"""
import shutil
from typing import Optional, List
from src.managers.base import PackageManager
from src.models.package import Package
from src.utils.shell import run_command
from src.utils.logger import logger

class WingetManager(PackageManager):
    """Gestor de paquetes para Windows usando winget"""

    @property
    def name(self) -> str:
        return "winget"

    def verify_availability(self) -> bool:
        """Verifica si winget está disponible"""
        if shutil.which("winget") is not None:
            return True
        code, _, _ = run_command(["winget", "--version"])
        return code == 0

    def is_installed(self, package_name: str) -> bool:
        """Verifica si un paquete está instalado por ID o por Nombre"""
        # Intentar por ID primero (coincidencia exacta)
        code, _, _ = run_command(["winget", "list", "-e", "--id", package_name])
        if code == 0:
            return True
        # Si falla, intentar por Nombre (coincidencia exacta)
        code, _, _ = run_command(["winget", "list", "-e", "--name", package_name])
        return code == 0

    def get_version(self, package_name: str) -> Optional[str]:
        """Obtiene la versión instalada de un paquete"""
        # Consultar por ID primero
        code, stdout, _ = run_command(["winget", "list", "-e", "--id", package_name])
        if code != 0:
            # Reintentar por nombre
            code, stdout, _ = run_command(["winget", "list", "-e", "--name", package_name])
            if code != 0:
                return None
        
        packages = self._parse_winget_list(stdout)
        if packages:
            return packages[0]["version"]
        return None

    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instala un paquete con winget de manera idempotente"""
        if self.is_installed(package.name):
            logger.info(f"✓ Paquete '{package.name}' ya está instalado.")
            return True
            
        cmd = ["winget", "install", "--id", package.name, "--silent", "--accept-package-agreements", "--accept-source-agreements"]
        if package.version and package.version != "latest":
            cmd.extend(["--version", package.version])
            
        if dry_run:
            logger.info(f"[DRY-RUN] Ejecutaría: {' '.join(cmd)}")
            return True
            
        logger.info(f"Instalando '{package.name}' vía winget...")
        code, stdout, stderr = run_command(cmd, timeout=600)
        if code == 0:
            logger.info(f"✓ Instalación de '{package.name}' completada exitosamente.")
            return True
        else:
            logger.error(f"❌ Error al instalar '{package.name}' vía winget. Código de salida: {code}")
            logger.error(f"Stderr: {stderr}")
            return False

    def _should_exclude(self, pkg_id: str, pkg_name: str, source: str) -> bool:
        """Determina si un paquete debe excluirse por ser ruido de sistema o runtime"""
        import re
        pkg_id_lower = pkg_id.lower()
        pkg_name_lower = pkg_name.lower()
        
        # 1. Limpiar el ID de prefijos comunes de winget (msix\ o arp\ o arp\machine\...)
        # para comparar de forma consistente.
        clean_id = pkg_id_lower
        for prefix in ("arp\\machine\\x64\\", "arp\\machine\\x86\\", "arp\\user\\x64\\", "arp\\user\\x86\\", "arp\\", "msix\\"):
            if clean_id.startswith(prefix):
                clean_id = clean_id[len(prefix):]
                
        # 2. Excluir si el ID o nombre indica que es una actualización KB de Windows
        if re.search(r'kb\d+', clean_id) or re.search(r'kb\d+', pkg_name_lower):
            return True
            
        # 3. Excluir si contiene llaves de GUID solas y no tiene un nombre amigable
        if re.match(r'^\{[0-9a-f-]+\}$', clean_id) and not pkg_name:
            return True

        # 4. Lista de aplicaciones predeterminadas de Windows y componentes del sistema (stubs/UWP preinstaladas)
        built_in_patterns = [
            "microsoft.microsoftedge",
            "microsoftedge",
            "microsoft.edge",
            "microsoft.onedrive",
            "microsoft.windowsterminal",
            "microsoft.wsl",
            "microsoft.teams",
            "microsoft.appinstaller",
            "microsoft.gameinput",
            "microsoft.sechealth",
            "microsoft.xbox",
            "microsoft.zune",
            "microsoft.skype",
            "microsoft.bing",
            "microsoft.getstarted",
            "microsoft.people",
            "microsoft.corporatecompanion",
            "microsoft.msn",
            "microsoft.screensketch",
            "microsoft.storepurchaseapp",
            "microsoft.windowsfeedbackhub",
            "microsoft.windowsmaps",
            "microsoft.windowsnotepad",
            "microsoft.windowscamera",
            "microsoft.windows.camera",
            "windowscamera",
            "microsoft.windowsalarms",
            "microsoft.windowsphone",
            "microsoft.yourphone",
            "microsoft.devhome",
            "microsoft.outlookforwindows",
            "microsoft.microsoftsolitairecollection",
            "microsoft.mixedreality.portal",
            "microsoft.office.onenote",
            "microsoft.paint",
            "microsoft.windowssoundrecorder",
            "microsoft.soundrecorder",
            "microsoftcorporationii",
            "microsoftwindows.client",
            "microsoftwindows.crossdevice",
            "widgetsplatform",
            "widgetsplatformruntime",
            "bingnews",
            "gethelp",
            "gamingapp",
            "gamingservices",
            "zunevideo",
            "zunemusic",
            "solitaire",
            "todos",
            "stickynotes",
            "quickassist",
            "family",
            "feedbackhub",
            "screenclip",
            "windowsstore",
            "visualstudiocodeinsiders",
            "microsoft.copilot",
            "microsoft copilot",
            "microsoft.windows.photos",
            "microsoft.windowsphotos",
            "microsoft.windowscalculator",
            "windowscalculator",
            "microsoft.windowscommunicationsapps",
            "windowscommunicationsapps",
            "microsoft.microsoftofficehub",
            "microsoftofficehub",
            "clipchamp",
            "microsoft.powerautomatedesktop",
            "powerautomatedesktop",
            "microsoft.startexperiencesapp",
            "startexperiencesapp"
        ]
        
        # Evitar capturar VS Code como MSIX redundante si ya se captura como winget standard
        # Comparamos contra el ID crudo en minúsculas
        if pkg_id_lower.startswith("msix\\microsoft.visualstudiocode"):
            return True

        for pattern in built_in_patterns:
            if pattern in clean_id or pattern in pkg_name_lower:
                return True

        # 5. Runtimes, SDKs, drivers y componentes de soporte/sistema
        runtime_patterns = [
            "microsoft.vcredist",
            "microsoft.vclibs",
            "microsoft.net.",
            "microsoft.windowsappruntime",
            "microsoft.winappruntime",
            "microsoft.ui.xaml",
            "microsoft.visualc",
            "microsoft.directx",
            "microsoft.dotnet.native.runtime",
            "microsoft.windowssdk.",
            "microsoft.xnaredist",
            "microsoft.msodbcsql",
            "microsoft.sqlserver.oledbdriver",
            "microsoft.webdeploy",
            "microsoft.msmpi",
            "microsoft.advertising",
            "microsoft.services.store.engagement",
            "hevcvideoextension",
            "heifimageextension",
            "vp9videoextensions",
            "webmediaextensions",
            "webimageextension",
            "rawimageextension",
            "microsoft.winget.source",
            "languagepack",
            "languageexperiencepack",
            "shellextension",
            "extension",
            "paquete de experiencia local",
            "experiencepack",
            "officepushnotification",
            "intel(r) software",
            "driver",
            "controller",
            "catalyst install manager",
            "nvidia control panel",
            "geforce experience",
            "realtek audio",
            "acuity assets",
            "finereader module",
            "coreeditorfonts",
            "sdk addon",
            "vss writer",
            "actionsserver",
            "visualstudio.installer",
            "visualstudioinstaller",
            "addin",
            "add-in",
            "clr types",
            "visual studio runtime"
        ]
        for rt in runtime_patterns:
            if rt in clean_id or rt in pkg_name_lower:
                return True
                
        return False

    def get_all_installed(self) -> List[Package]:
        """Lista todos los paquetes instalados por winget en el sistema"""
        code, stdout, _ = run_command(["winget", "list"])
        if code != 0:
            return []
            
        parsed = self._parse_winget_list(stdout)
        packages = []
        for item in parsed:
            if self._should_exclude(item["id"], item["name"], item["source"]):
                continue
            packages.append(Package(
                name=item["id"],
                manager="winget",
                version=item["version"],
                description=f"App: {item['name']}",
                repository=item["source"] if item["source"] else "local"
            ))
        return packages

    def _parse_winget_list(self, stdout: str) -> List[dict]:
        """Parsea la salida de winget list basada en columnas fijas"""
        lines = stdout.splitlines()
        header_idx = -1
        for idx, line in enumerate(lines):
            has_name = "Nombre" in line or "Name" in line
            has_id = "Id" in line
            has_version = "Versión" in line or "Version" in line or "Versi" in line
            if has_name and has_id and has_version:
                header_idx = idx
                break
                
        if header_idx == -1:
            return []
            
        header_line = lines[header_idx]
        idx_name = header_line.find("Nombre")
        if idx_name == -1:
            idx_name = header_line.find("Name")
            
        idx_id = header_line.find("Id")
        
        idx_version = header_line.find("Versión")
        if idx_version == -1:
            idx_version = header_line.find("Version")
        if idx_version == -1:
            idx_version = header_line.find("Versi")
            
        idx_available = header_line.find("Disponible")
        if idx_available == -1:
            idx_available = header_line.find("Available")
        if idx_available == -1:
            idx_available = header_line.find("Dispon")
            
        idx_source = header_line.find("Origen")
        if idx_source == -1:
            idx_source = header_line.find("Source")
        
        packages = []
        for line in lines[header_idx + 2:]:
            if not line.strip() or line.startswith("<") or "-----" in line:
                continue
            
            # Cortar según los índices de columnas
            name = line[idx_name:idx_id].strip() if idx_id != -1 else line.strip()
            id_val = line[idx_id:idx_version].strip() if idx_version != -1 else ""
            
            version_end = idx_available if idx_available != -1 else len(line)
            version = line[idx_version:version_end].strip() if idx_version != -1 else ""
            
            source = ""
            if idx_source != -1 and len(line) > idx_source:
                source = line[idx_source:].strip()
                
            if name and id_val:
                # Limpiar posibles caracteres de truncamiento de consola al final
                name = name.rstrip(" \t.\u2026\ufffd")
                id_val = id_val.rstrip(" \t.\u2026\ufffd")
                version = version.rstrip(" \t.\u2026\ufffd")
                source = source.rstrip(" \t.\u2026\ufffd")
                
                packages.append({
                    "name": name,
                    "id": id_val,
                    "version": version,
                    "source": source
                })
        return packages
