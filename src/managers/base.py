"""
Clase base abstracta para los gestores de paquetes - PRD §RT-5
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from src.models.package import Package

class PackageManager(ABC):
    """Base class para todos los gestores de paquetes"""
    
    @abstractmethod
    def is_installed(self, package_name: str) -> bool:
        """Verificar si la aplicación está instalada"""
        pass
    
    @abstractmethod
    def install(self, package: Package, dry_run: bool = False) -> bool:
        """Instalar la aplicación (idempotente)"""
        pass
    
    @abstractmethod
    def get_version(self, package_name: str) -> Optional[str]:
        """Obtener la versión instalada de una aplicación"""
        pass
    
    @abstractmethod
    def get_all_installed(self) -> List[Package]:
        """Retorna la lista de todos los paquetes instalados por este gestor"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del manager: 'apt', 'brew', 'winget', etc."""
        pass
    
    @abstractmethod
    def verify_availability(self) -> bool:
        """Verificar si el gestor está disponible y configurado en este sistema operativo"""
        pass
