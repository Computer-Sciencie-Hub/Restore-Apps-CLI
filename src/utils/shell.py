"""
Módulo de ejecución de comandos del sistema - PRD §RT-1
"""
import subprocess
import os
from typing import List, Tuple, Optional, Union
from src.utils.logger import logger

def run_command(
    cmd: Union[str, List[str]], 
    timeout: int = 300, 
    shell: bool = False,
    env: Optional[dict] = None
) -> Tuple[int, str, str]:
    """
    Ejecuta un comando del sistema de forma segura.
    Retorna (exit_code, stdout, stderr)
    """
    try:
        # Combinar entorno actual con variables adicionales
        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)
            
        # Ejecución del comando
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            timeout=timeout,
            env=execution_env
        )
        
        def decode_bytes(data: bytes) -> str:
            if not data:
                return ""
            for enc in ("utf-8", "cp1252", "cp850"):
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="replace")
            
        return result.returncode, decode_bytes(result.stdout), decode_bytes(result.stderr)
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Límite de tiempo excedido para: {cmd}")
        return -1, "", f"TimeoutExpired: {str(e)}"
    except Exception as e:
        logger.error(f"Error al ejecutar: {cmd} - {str(e)}")
        return -1, "", str(e)
