"""
Modelo de Manifest - PRD §📋
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import yaml
import os
import re
from src.models.package import Package, DotFile

@dataclass
class Manifest:
    """Modelo del Manifiesto - PRD §📋"""
    version: str = "1.0"
    metadata: Dict = field(default_factory=dict)
    system: Dict = field(default_factory=dict)
    packages: List[Package] = field(default_factory=list)
    dotfiles: List[DotFile] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, file_path: str) -> 'Manifest':
        """PRD §RF-4: Parsear YAML a Manifest"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Manifest file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # Parse packages
        packages = []
        for pkg_data in data.get("packages", []):
            packages.append(Package(
                name=pkg_data.get("name"),
                manager=pkg_data.get("manager"),
                version=pkg_data.get("version", "latest"),
                tier=pkg_data.get("tier", 2),
                depends_on=pkg_data.get("depends_on", []),
                post_install=pkg_data.get("post_install", []),
                description=pkg_data.get("description", ""),
                repository=pkg_data.get("repository", "")
            ))

        # Parse dotfiles
        dotfiles = []
        for df_data in data.get("dotfiles", []):
            dotfiles.append(DotFile(
                source_path=df_data.get("source_path"),
                destination_path=df_data.get("destination_path"),
                is_secret=df_data.get("is_secret", False),
                create_symlink=df_data.get("create_symlink", False),
                permissions=df_data.get("permissions", "0644"),
                skip_if_exists=df_data.get("skip_if_exists", False),
                checksum=df_data.get("checksum", "")
            ))

        return cls(
            version=str(data.get("version", "1.0")),
            metadata=data.get("metadata", {}),
            system=data.get("system", {}),
            packages=packages,
            dotfiles=dotfiles
        )

    def to_yaml(self, file_path: str) -> None:
        """PRD §RF-4: Serializar Manifest a YAML"""
        data = {
            "version": self.version,
            "metadata": self.metadata,
            "system": self.system,
            "packages": [p.to_dict() for p in self.packages],
            "dotfiles": [d.to_dict() for d in self.dotfiles]
        }
        
        # Asegurar que el directorio padre exista
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def validate(self) -> List[str]:
        """PRD §🔍: Validar integridad y coherencia referencial"""
        errors = []
        
        # 1. Validar versión
        if not re.match(r"^\d+\.\d+$", self.version):
            errors.append(f"Invalid version format: '{self.version}'. Must be 'X.Y'")

        # 2. Validar campos requeridos de metadata
        required_metadata = {"os", "arch", "timestamp"}
        missing_metadata = required_metadata - set(self.metadata.keys())
        if missing_metadata:
            errors.append(f"Missing required metadata fields: {', '.join(missing_metadata)}")

        # 3. Validar consistencia de dependencias de paquetes (integrity checks)
        package_names = {pkg.name for pkg in self.packages}
        for pkg in self.packages:
            try:
                pkg.__post_init__()
            except ValueError as e:
                errors.append(f"Package '{pkg.name}': {str(e)}")
                
            if pkg.depends_on:
                for dep in pkg.depends_on:
                    if dep not in package_names:
                        errors.append(
                            f"Package '{pkg.name}' depends on '{dep}' "
                            f"which doesn't exist in the package list."
                        )

        # 4. Validar dotfiles
        for df in self.dotfiles:
            try:
                df.__post_init__()
            except ValueError as e:
                errors.append(f"DotFile '{df.source_path}': {str(e)}")

        return errors
