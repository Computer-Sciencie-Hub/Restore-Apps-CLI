"""
Resolutor de dependencias con Topological Sort - PRD §RT-4
"""
from typing import List, Dict, Set
from src.models.package import Package

class DependencyResolver:
    """Resuelve el orden de instalación basándose en Tiers y dependencias - PRD §RT-4"""
    
    def topological_sort(self, packages: List[Package]) -> List[Package]:
        """
        Calcula un orden seguro de instalación usando el algoritmo de Kahn.
        Prioriza los paquetes con menor tier y desempata alfabéticamente.
        """
        pkg_map = {pkg.name: pkg for pkg in packages}
        
        # 1. Construir el grafo de adyacencia e in-degrees
        adj: Dict[str, Set[str]] = {pkg.name: set() for pkg in packages}
        in_degree: Dict[str, int] = {pkg.name: 0 for pkg in packages}
        
        for pkg in packages:
            for dep in pkg.depends_on:
                if dep in pkg_map:
                    adj[dep].add(pkg.name)
                    in_degree[pkg.name] += 1
                    
        # 2. Obtener nodos sin prerequisitos (in-degree == 0)
        ready = [pkg_map[name] for name, deg in in_degree.items() if deg == 0]
        # Ordenar por tier (1 -> 2 -> 3) y alfabéticamente por nombre
        ready.sort(key=lambda p: (p.tier, p.name))
        
        result: List[Package] = []
        
        while ready:
            curr = ready.pop(0)
            result.append(curr)
            
            # Decrementar in-degree de los dependientes
            for neighbor in adj[curr.name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    ready.append(pkg_map[neighbor])
                    
            # Mantener lista ordenada por tier y alfabéticamente
            ready.sort(key=lambda p: (p.tier, p.name))
            
        # 3. Validar si hay ciclos (si no se procesaron todos los paquetes)
        if len(result) != len(packages):
            cycles = self.detect_cycles(packages)
            raise ValueError(f"Ciclo de dependencias detectado: {cycles}")
            
        return result

    def detect_cycles(self, packages: List[Package]) -> List[List[str]]:
        """
        Detecta ciclos de dependencias circulares mediante búsqueda en profundidad (DFS).
        """
        pkg_map = {pkg.name: pkg for pkg in packages}
        visited = {} # name -> estado: 0=no_visitado, 1=visitando, 2=visitado
        cycles = []
        
        def dfs(name: str, path: List[str]):
            visited[name] = 1 # Marcado como en proceso
            path.append(name)
            
            pkg = pkg_map.get(name)
            if pkg:
                for dep in pkg.depends_on:
                    if dep not in pkg_map:
                        continue
                    if visited.get(dep, 0) == 1:
                        # Se cerró el ciclo
                        start_idx = path.index(dep)
                        cycles.append(path[start_idx:] + [dep])
                    elif visited.get(dep, 0) == 0:
                        dfs(dep, path)
                        
            path.pop()
            visited[name] = 2 # Marcado como completado
            
        for pkg in packages:
            if visited.get(pkg.name, 0) == 0:
                dfs(pkg.name, [])
                
        return cycles

    def validate_dependencies(self, packages: List[Package]) -> bool:
        """Verifica si un listado de paquetes es libre de ciclos"""
        try:
            self.topological_sort(packages)
            return True
        except ValueError:
            return False
