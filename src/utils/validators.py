"""
Esquemas de validación Pydantic para el Manifiesto - PRD §🔍
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
import re

class PackageSchema(BaseModel):
    name: str = Field(..., min_length=1)
    manager: str
    version: str = "latest"
    tier: int = Field(2, ge=1, le=3)
    depends_on: Optional[List[str]] = Field(default_factory=list)
    post_install: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = ""
    repository: Optional[str] = ""

    @field_validator("manager")
    @classmethod
    def validate_manager(cls, v: str) -> str:
        valid_managers = {"apt", "brew", "flatpak", "snap", "winget", "pip", "npm", "chocolatey", "scoop", "mas"}
        if v.lower() not in valid_managers:
            raise ValueError(f"Invalid manager '{v}'. Valid options: {valid_managers}")
        return v.lower()

class DotfileSchema(BaseModel):
    source_path: str = Field(..., min_length=1)
    destination_path: Optional[str] = None
    is_secret: bool = False
    create_symlink: bool = False
    permissions: str = "0644"
    skip_if_exists: bool = False
    checksum: Optional[str] = ""

class MetadataSchema(BaseModel):
    os: str
    arch: str
    timestamp: str
    hostname: Optional[str] = "unknown"
    user: Optional[str] = "root"

    @field_validator("os")
    @classmethod
    def validate_os(cls, v: str) -> str:
        valid_os = {"ubuntu", "debian", "macos", "windows", "fedora", "arch", "linux"}
        for o in valid_os:
            if v.lower().startswith(o):
                return v
        return v # Permitir otros, pero advertir o pasar

class ManifestSchema(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+$")
    metadata: MetadataSchema
    system: Optional[Dict[str, str]] = Field(default_factory=dict)
    packages: List[PackageSchema] = Field(default_factory=list)
    dotfiles: List[DotfileSchema] = Field(default_factory=list)


def validate_manifest_dict(data: dict) -> List[str]:
    """
    Valida un diccionario de manifiesto contra el esquema Pydantic.
    Retorna la lista de errores formateados (vacía si es válido).
    """
    errors = []
    try:
        ManifestSchema(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"[{loc}]: {msg}")
    return errors
