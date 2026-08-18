"""
Gestor de Dotfiles (Configuraciones) - PRD §RT-1
"""
import os
import shutil
import hashlib
import datetime
from typing import List, Dict, Tuple
from src.models.package import DotFile
from src.utils.logger import logger

class DotfileManager:
    """Administra la verificación y aplicación de dotfiles - PRD §RT-1"""

    def __init__(self, manifest_dir: str = "."):
        self.manifest_dir = os.path.abspath(manifest_dir)

    def calculate_sha256(self, file_path: str) -> str:
        """Calcula el hash SHA256 de un archivo"""
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return ""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash para {file_path}: {e}")
            return ""

    def get_paths(self, dotfile: DotFile) -> Tuple[str, str]:
        """Retorna rutas absolutas (origen, destino)"""
        # El origen es relativo al directorio del manifiesto
        src = os.path.abspath(os.path.join(self.manifest_dir, dotfile.source_path))
        # El destino expande el home directory (~ / %USERPROFILE%)
        dst = os.path.abspath(os.path.expanduser(dotfile.destination_path))
        return src, dst

    def check_security(self, src: str, dst: str) -> None:
        """
        Verifica la seguridad de las rutas para prevenir Path Traversal y Symlink Hijacking.
        Lanza PermissionError en caso de detectar riesgos de seguridad.
        """
        # 1. Evitar Symlink Hijacking en origen (src)
        # Si el archivo origen en el repositorio es un enlace simbólico, abortar.
        if os.path.islink(src):
            raise PermissionError(f"Riesgo de seguridad: El origen del dotfile '{src}' es un enlace simbólico.")

        # 2. Evitar Path Traversal en destino (dst)
        # No usar startswith: un directorio hermano (ej. "C:\Users\japer_evil")
        # comparte el prefijo de string con el home sin estar realmente dentro de él.
        home = os.path.abspath(os.path.expanduser("~"))
        real_dst = os.path.abspath(dst)
        home_cmp = os.path.normcase(home)
        dst_cmp = os.path.normcase(real_dst)
        try:
            common = os.path.commonpath([home_cmp, dst_cmp])
        except ValueError:
            # Rutas en unidades/raíces distintas (ej. C:\ vs D:\): fuera del home
            common = None
        if common != home_cmp:
            raise PermissionError(f"Riesgo de seguridad: El destino '{dst}' está fuera del directorio del usuario '{home}'.")

    def verify_dotfile(self, dotfile: DotFile) -> str:
        """
        Verifica el estado de un dotfile.
        Retorna: 'OK', 'MISSING', 'MODIFIED' (si difiere el checksum).
        """
        src, dst = self.get_paths(dotfile)
        self.check_security(src, dst)
        
        if not os.path.exists(src):
            return "SOURCE_MISSING"
            
        if not os.path.exists(dst):
            return "MISSING"

        src_hash = self.calculate_sha256(src)
        dst_hash = self.calculate_sha256(dst)
        
        # Guardar checksum calculado en el modelo si no lo tenía
        if not dotfile.checksum:
            dotfile.checksum = src_hash

        if src_hash != dst_hash:
            return "MODIFIED"
            
        return "OK"

    def backup_file(self, file_path: str) -> str:
        """Crea una copia de seguridad del archivo existente"""
        if not os.path.exists(file_path):
            return ""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup.{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Respaldo creado: {os.path.basename(file_path)} -> {os.path.basename(backup_path)}")
            return backup_path
        except Exception as e:
            logger.error(f"No se pudo respaldar {file_path}: {e}")
            return ""

    def apply_dotfile(self, dotfile: DotFile, backup: bool = True, force: bool = False) -> bool:
        """
        Aplica un dotfile (copia o crea symlink).
        Retorna True si se aplicó con éxito o no requería cambios.
        """
        src, dst = self.get_paths(dotfile)
        
        if not os.path.exists(src):
            logger.error(f"El archivo origen del dotfile no existe: {src}")
            return False

        status = self.verify_dotfile(dotfile)
        
        if status == "OK" and not force:
            logger.info(f"✓ Dotfile ya sincronizado: {dotfile.source_path}")
            return True

        if status == "MODIFIED" or status == "MISSING":
            if os.path.exists(dst):
                if dotfile.skip_if_exists and not force:
                    logger.info(f"⏭️ Omitiendo dotfile (skip_if_exists): {dotfile.source_path}")
                    return True
                if backup:
                    self.backup_file(dst)
                    
            # Asegurar que el directorio destino exista
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # Remover enlace o archivo previo si existía
            if os.path.exists(dst) or os.path.islink(dst):
                if os.path.isdir(dst) and not os.path.islink(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)

            # Intentar symlink si está configurado
            if dotfile.create_symlink:
                try:
                    os.symlink(src, dst)
                    logger.info(f"✓ Symlink creado: {dotfile.source_path} -> {dotfile.destination_path}")
                    return True
                except OSError as e:
                    logger.warning(f"No se pudo crear symlink (permisos/SO), copiando en su lugar: {e}")
            
            # Copiar archivo
            try:
                shutil.copy2(src, dst)
                # Aplicar permisos si es Linux/macOS
                if os.name != 'nt' and dotfile.permissions:
                    # Convertir permisos octales (ej. '0600' -> 384)
                    perms = int(dotfile.permissions, 8)
                    os.chmod(dst, perms)
                logger.info(f"✓ Archivo copiado: {dotfile.source_path} -> {dotfile.destination_path}")
                return True
            except Exception as e:
                logger.error(f"Fallo al copiar archivo {dotfile.source_path}: {e}")
                return False
                
        return False
