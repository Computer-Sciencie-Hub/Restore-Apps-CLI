"""
Modelos de datos de Package y DotFile - PRD §📋
"""
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Package:
    """Modelo de Paquete - PRD §📋"""
    name: str
    manager: str
    version: str = "latest"
    tier: int = 2
    depends_on: List[str] = field(default_factory=list)
    post_install: List[str] = field(default_factory=list)
    description: str = ""
    repository: str = ""

    VALID_MANAGERS = {"apt", "brew", "flatpak", "snap", "winget", "pip", "npm", "chocolatey", "scoop", "mas"}
    VALID_TIERS = {1, 2, 3}

    def __post_init__(self):
        """Validación post-inicialización"""
        if not self.name or len(self.name) < 1:
            raise ValueError("Package name cannot be empty")
        if self.manager not in self.VALID_MANAGERS:
            raise ValueError(
                f"Invalid manager '{self.manager}'. "
                f"Must be one of {self.VALID_MANAGERS}"
            )
        if self.tier not in self.VALID_TIERS:
            raise ValueError(f"Invalid tier {self.tier}. Must be 1, 2, or 3")
        
        # Asegurar tipos correctos para listas que provienen de YAML
        if self.depends_on is None:
            self.depends_on = []
        elif not isinstance(self.depends_on, list):
            self.depends_on = [self.depends_on]
            
        if self.post_install is None:
            self.post_install = []
        elif not isinstance(self.post_install, list):
            self.post_install = [self.post_install]

    def __hash__(self):
        return hash(f"{self.manager}:{self.name}")

    def __eq__(self, other):
        if isinstance(other, Package):
            return self.manager == other.manager and self.name == other.name
        return False
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "manager": self.manager,
            "version": self.version,
            "tier": self.tier,
            "depends_on": self.depends_on,
            "post_install": self.post_install,
            "description": self.description,
            "repository": self.repository,
        }


@dataclass
class DotFile:
    """Modelo de Dotfile - PRD §📋"""
    source_path: str
    destination_path: Optional[str] = None
    is_secret: bool = False
    create_symlink: bool = False
    permissions: str = "0644"
    skip_if_exists: bool = False
    checksum: str = ""

    def __post_init__(self):
        if not self.source_path:
            raise ValueError("source_path cannot be empty")
        if not self.destination_path:
            self.destination_path = self.source_path

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "is_secret": self.is_secret,
            "create_symlink": self.create_symlink,
            "permissions": self.permissions,
            "skip_if_exists": self.skip_if_exists,
            "checksum": self.checksum,
        }
