#!/usr/bin/env python3
"""
PRD Tooling - Utilidades para trabajar con el PRD de dotenv-manager

Funcionalidades:
- Validar manifesto YAML contra esquema PRD
- Generar boilerplate de código
- Extraer ejemplos del PRD
- Validar seguridad de manifesto
"""

import json
import yaml
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# MODELOS DE DATOS (Basados en PRD)
# ============================================================================

class Tier(Enum):
    CRITICAL = 1
    IMPORTANT = 2
    OPTIONAL = 3

@dataclass
class Package:
    """Modelo de Paquete del PRD"""
    name: str
    manager: str  # apt, brew, flatpak, snap, winget, pip, npm
    version: str = "latest"
    tier: int = 2
    depends_on: Optional[List[str]] = None
    post_install: Optional[List[str]] = None
    description: str = ""
    repository: str = ""

    VALID_MANAGERS = {"apt", "brew", "flatpak", "snap", "winget", "pip", "npm"}
    VALID_TIERS = {1, 2, 3}

    def validate(self) -> List[str]:
        """Retorna lista de errores de validación"""
        errors = []
        
        if not self.name or len(self.name) < 1:
            errors.append(f"Package name cannot be empty")
        
        if self.manager not in self.VALID_MANAGERS:
            errors.append(
                f"Invalid manager '{self.manager}'. "
                f"Valid: {', '.join(self.VALID_MANAGERS)}"
            )
        
        if self.tier not in self.VALID_TIERS:
            errors.append(f"Invalid tier {self.tier}. Must be 1, 2, or 3")
        
        return errors


@dataclass
class DotFile:
    """Modelo de Dotfile del PRD"""
    source_path: str
    destination_path: Optional[str] = None
    is_secret: bool = False
    create_symlink: bool = False
    permissions: str = "0644"
    skip_if_exists: bool = False
    checksum: str = ""

    def validate(self) -> List[str]:
        errors = []
        if not self.source_path:
            errors.append("source_path cannot be empty")
        return errors


@dataclass
class Manifest:
    """Modelo de Manifest del PRD"""
    version: str
    metadata: Dict
    system: Dict
    packages: List[Package]
    dotfiles: List[DotFile]

    def validate(self) -> List[str]:
        """Validación completa del manifesto"""
        errors = []

        # Validar versión
        if not re.match(r"^\d+\.\d+$", self.version):
            errors.append(f"Invalid version format: {self.version}")

        # Validar metadata
        required_metadata = {"os", "arch", "timestamp"}
        if not required_metadata.issubset(self.metadata.keys()):
            missing = required_metadata - set(self.metadata.keys())
            errors.append(f"Missing metadata fields: {missing}")

        # Validar cada paquete
        for pkg in self.packages:
            pkg_errors = pkg.validate()
            errors.extend([f"Package '{pkg.name}': {err}" for err in pkg_errors])

        # Validar dependencias (existen los paquetes referenciados)
        package_names = {pkg.name for pkg in self.packages}
        for pkg in self.packages:
            if pkg.depends_on:
                for dep in pkg.depends_on:
                    if dep not in package_names:
                        errors.append(
                            f"Package '{pkg.name}' depends on '{dep}' "
                            f"which doesn't exist in manifest"
                        )

        # Validar dotfiles
        for df in self.dotfiles:
            df_errors = df.validate()
            errors.extend([f"DotFile '{df.source_path}': {err}" for err in df_errors])

        return errors


# ============================================================================
# DETECCIÓN DE SECRETOS
# ============================================================================

class SecretDetector:
    """Detecta credenciales en manifesto"""

    SECRET_PATTERNS = [
        (r"AZURE_SUBSCRIPTION_ID", "Azure Subscription ID"),
        (r"aws_access_key_id", "AWS Access Key"),
        (r"password\s*[=:]", "Password field"),
        (r"token\s*[=:]", "Token field"),
        (r"api[_-]?key", "API Key"),
        (r"secret[_-]?key", "Secret Key"),
        (r"private[_-]?key", "Private Key"),
        (r"api[_-]?token", "API Token"),
        (r"Bearer\s+[A-Za-z0-9\-_.]+", "Bearer Token"),
        (r"[A-Za-z0-9\-_.]+@[A-Za-z0-9\-_.]+\.[A-Za-z0-9\-_.]+:[A-Za-z0-9\-_.]+",
         "SSH Key Pattern"),
    ]

    @classmethod
    def check_manifest(cls, manifest_dict: Dict) -> List[Tuple[str, str]]:
        """
        Escanea manifesto y retorna lista de (ubicación, tipo_secret)
        """
        findings = []

        def scan_value(value, path=""):
            if isinstance(value, str):
                for pattern, secret_type in cls.SECRET_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        findings.append((path, secret_type))
            elif isinstance(value, dict):
                for key, val in value.items():
                    scan_value(val, f"{path}.{key}")
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    scan_value(item, f"{path}[{idx}]")

        scan_value(manifest_dict)
        return findings


# ============================================================================
# VALIDADOR DE MANIFESTO YAML
# ============================================================================

class ManifestValidator:
    """Valida manifesto YAML contra esquema PRD"""

    @staticmethod
    def from_yaml(file_path: str) -> Manifest:
        """Parsea YAML a Manifest"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        return ManifestValidator.dict_to_manifest(data)

    @staticmethod
    def dict_to_manifest(data: Dict) -> Manifest:
        """Convierte dict a Manifest"""
        packages = []
        if "packages" in data:
            for pkg_data in data.get("packages", []):
                packages.append(Package(**pkg_data))

        dotfiles = []
        if "dotfiles" in data:
            for df_data in data.get("dotfiles", []):
                dotfiles.append(DotFile(**df_data))

        return Manifest(
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
            system=data.get("system", {}),
            packages=packages,
            dotfiles=dotfiles,
        )

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, List[str]]:
        """
        Valida archivo YAML manifesto
        Retorna (is_valid, list_of_errors)
        """
        try:
            manifest = ManifestValidator.from_yaml(file_path)
            errors = manifest.validate()
            return len(errors) == 0, errors
        except Exception as e:
            return False, [f"YAML parsing error: {str(e)}"]

    @staticmethod
    def check_secrets(file_path: str) -> List[Tuple[str, str]]:
        """Detecta potenciales secretos en manifesto"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return SecretDetector.check_manifest(data)


# ============================================================================
# GENERADOR DE BOILERPLATE
# ============================================================================

class BoilerplateGenerator:
    """Genera estructura base de código desde el PRD"""

    @staticmethod
    def generate_project_structure(output_dir: str = ".") -> None:
        """Crea estructura de directorios"""
        dirs = [
            "src/core",
            "src/managers",
            "src/models",
            "src/utils",
            "tests",
            "tests/fixtures",
        ]

        for d in dirs:
            Path(output_dir) / d
            print(f"mkdir -p {d}")

    @staticmethod
    def generate_requirements_txt() -> str:
        """Genera requirements.txt desde PRD"""
        return """# Core dependencies
click>=8.1.7
pyyaml>=6.0
packaging>=23.0
psutil>=5.9.0
pydantic>=2.0
requests>=2.31.0
python-dotenv>=1.0
colorama>=0.4.6
typer>=0.9.0

# Dev dependencies
pytest>=7.4.0
pytest-mock>=3.11.1
black>=23.0
flake8>=6.0
mypy>=1.0
"""

    @staticmethod
    def generate_package_dataclass() -> str:
        """Genera dataclass Package"""
        return '''"""
Modelos de datos basados en PRD
"""
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Package:
    """Modelo de Paquete - PRD §RT-1"""
    name: str
    manager: str
    version: str = "latest"
    tier: int = 2
    depends_on: Optional[List[str]] = None
    post_install: Optional[List[str]] = None
    description: str = ""
    repository: str = ""
    
    VALID_MANAGERS = {"apt", "brew", "flatpak", "snap", "winget", "pip", "npm"}
    VALID_TIERS = {1, 2, 3}
    
    def __post_init__(self):
        """Validación post-inicialización"""
        if self.manager not in self.VALID_MANAGERS:
            raise ValueError(
                f"Invalid manager: {self.manager}. "
                f"Must be one of {self.VALID_MANAGERS}"
            )
        if self.tier not in self.VALID_TIERS:
            raise ValueError(f"Invalid tier: {self.tier}. Must be 1, 2, or 3")
    
    def __hash__(self):
        return hash(f"{self.manager}:{self.name}")
    
    def __eq__(self, other):
        if isinstance(other, Package):
            return self.manager == other.manager and self.name == other.name
        return False


@dataclass
class DotFile:
    """Modelo de Dotfile - PRD §RT-1"""
    source_path: str
    destination_path: Optional[str] = None
    is_secret: bool = False
    create_symlink: bool = False
    permissions: str = "0644"
    skip_if_exists: bool = False
    checksum: str = ""


@dataclass
class Manifest:
    """Modelo de Manifest - PRD §RT-1"""
    version: str
    metadata: dict
    system: dict
    packages: List[Package] = field(default_factory=list)
    dotfiles: List[DotFile] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, file_path: str) -> "Manifest":
        """PRD §RF-4: Parsear YAML a Manifest"""
        import yaml
        with open(file_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, file_path: str) -> None:
        """PRD §RF-4: Serializar Manifest a YAML"""
        import yaml
        with open(file_path, 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)
    
    def validate(self) -> List[str]:
        """PRD §RNF-4: Validar integridad de manifest"""
        errors = []
        # TODO: Implementar validaciones
        return errors
'''

    @staticmethod
    def generate_sample_manifest() -> str:
        """Genera manifesto YAML de ejemplo"""
        return '''# dotenv-manager Manifest - Sistema Setup PC
# PRD Reference: https://github.com/your-org/dotenv-manager/blob/main/SYSTEM_SETUP_PRD.md

version: "1.0"

metadata:
  os: "ubuntu-22.04"
  arch: "x86_64"
  timestamp: "2024-01-15T14:30:00Z"
  hostname: "perez-dev-machine"
  user: "perez"

system:
  locale: "es_SV.UTF-8"
  timezone: "America/El_Salvador"

packages:
  # TIER 1: Dependencias críticas - PRD §RF-2
  - name: "build-essential"
    manager: "apt"
    version: "12.9"
    tier: 1
    description: "Essential build tools"
    
  - name: "python3.11"
    manager: "apt"
    version: "3.11.7"
    tier: 1
    post_install:
      - "python3.11 -m pip install --upgrade pip"
      - "python3.11 -m pip install virtualenv"
    
  - name: "git"
    manager: "apt"
    version: "2.40.0"
    tier: 1
    post_install:
      - "git config --global user.name 'Perez'"
      - "git config --global user.email 'perez@example.com'"
  
  # TIER 2: Aplicaciones principales
  - name: "docker.io"
    manager: "apt"
    version: "24.0.1"
    tier: 2
    depends_on: ["build-essential"]
    description: "Container runtime"
    post_install:
      - "sudo usermod -aG docker $USER"
      - "sudo systemctl enable docker"
  
  - name: "vscode"
    manager: "flatpak"
    version: "latest"
    tier: 2
    description: "Code editor"
    post_install:
      - "code --install-extension ms-python.python"
      - "code --install-extension ms-vscode.remote-remote-ssh"
  
  # TIER 3: Aplicaciones opcionales
  - name: "teams"
    manager: "snap"
    version: "latest"
    tier: 3

# Configuraciones a restaurar
dotfiles:
  - source_path: ".bashrc"
    destination_path: "~/.bashrc"
    is_secret: false
    skip_if_exists: false
  
  - source_path: ".config/code/settings.json"
    destination_path: "~/.config/Code/User/settings.json"
    is_secret: false
  
  - source_path: ".gitconfig"
    destination_path: "~/.gitconfig"
    is_secret: false
    skip_if_exists: true
  
  - source_path: ".ssh/config"
    destination_path: "~/.ssh/config"
    is_secret: false
    permissions: "0600"
    skip_if_exists: true
'''


# ============================================================================
# CLI - Interfaz de línea de comandos
# ============================================================================

class CLI:
    """Utilidad de línea de comandos para PRD"""

    @staticmethod
    def validate_manifest(manifest_file: str) -> None:
        """Valida manifesto YAML"""
        print(f"\n📋 Validando manifesto: {manifest_file}")
        print("-" * 60)

        is_valid, errors = ManifestValidator.validate_file(manifest_file)

        if is_valid:
            print("✅ Manifesto válido")
        else:
            print(f"❌ {len(errors)} errores encontrados:\n")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            sys.exit(1)

        # Detectar secretos
        secrets = ManifestValidator.check_secrets(manifest_file)
        if secrets:
            print(f"\n⚠️  Posibles secretos detectados ({len(secrets)}):")
            for location, secret_type in secrets:
                print(f"  - {location}: {secret_type}")
            print("\n  ⚠️  Considere excluir estos campos del manifesto")
        else:
            print("✅ No se detectaron secretos")

    @staticmethod
    def generate_boilerplate(output_dir: str = ".") -> None:
        """Genera boilerplate de proyecto"""
        print("\n🔧 Generando boilerplate...")
        print("-" * 60)

        # Crear directorios
        print("\n📁 Creando estructura de directorios:")
        Path(output_dir).mkdir(exist_ok=True)
        dirs = [
            "src/core",
            "src/managers",
            "src/models",
            "src/utils",
            "tests/fixtures",
        ]
        for d in dirs:
            Path(output_dir) / d
            (Path(output_dir) / d).mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {d}/")

        # Generar requirements.txt
        print("\n📦 Generando requirements.txt")
        req_file = Path(output_dir) / "requirements.txt"
        req_file.write_text(BoilerplateGenerator.generate_requirements_txt())
        print(f"  ✓ {req_file}")

        # Generar models.py
        print("\n📝 Generando models.py")
        models_file = Path(output_dir) / "src" / "models" / "package.py"
        models_file.write_text(BoilerplateGenerator.generate_package_dataclass())
        print(f"  ✓ {models_file}")

        # Generar sample manifest
        print("\n📋 Generando sample manifest")
        manifest_file = Path(output_dir) / "sample_manifest.yaml"
        manifest_file.write_text(BoilerplateGenerator.generate_sample_manifest())
        print(f"  ✓ {manifest_file}")

        print("\n✅ Boilerplate generado exitosamente")
        print(f"\n📖 Próximos pasos:")
        print(f"  1. Instalar dependencias: pip install -r requirements.txt")
        print(f"  2. Editar sample_manifest.yaml con tus aplicaciones")
        print(f"  3. Validar: python prd_tooling.py validate sample_manifest.yaml")

    @staticmethod
    def extract_examples() -> None:
        """Extrae ejemplos del PRD"""
        print("\n📚 Ejemplos del PRD:")
        print("-" * 60)
        print(BoilerplateGenerator.generate_sample_manifest())

    @staticmethod
    def generate_example_manifest(output_file: str = "my_setup.yaml") -> None:
        """Genera manifest de ejemplo"""
        print(f"\n📋 Generando manifest de ejemplo: {output_file}")
        Path(output_file).write_text(
            BoilerplateGenerator.generate_sample_manifest()
        )
        print(f"✅ Archivo creado: {output_file}")
        print(f"   Próximo paso: editar manualmente y validar con:")
        print(f"   python prd_tooling.py validate {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Herramientas para trabajar con PRD de dotenv-manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando")

    # Comando: validate
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validar manifesto YAML contra esquema PRD"
    )
    validate_parser.add_argument("manifest_file", help="Ruta a manifesto YAML")

    # Comando: generate
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generar boilerplate de proyecto"
    )
    generate_parser.add_argument(
        "--output-dir",
        default=".",
        help="Directorio de salida (default: .)"
    )

    # Comando: example
    example_parser = subparsers.add_parser(
        "example",
        help="Generar manifest de ejemplo"
    )
    example_parser.add_argument(
        "--output",
        default="my_setup.yaml",
        help="Archivo de salida (default: my_setup.yaml)"
    )

    # Comando: examples
    subparsers.add_parser(
        "examples",
        help="Mostrar ejemplos del PRD"
    )

    args = parser.parse_args()

    if args.command == "validate":
        CLI.validate_manifest(args.manifest_file)
    elif args.command == "generate":
        CLI.generate_boilerplate(args.output_dir)
    elif args.command == "example":
        CLI.generate_example_manifest(args.output)
    elif args.command == "examples":
        CLI.extract_examples()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
