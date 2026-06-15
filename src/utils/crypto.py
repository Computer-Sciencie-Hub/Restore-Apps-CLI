"""
Módulo de detección de secretos - PRD §RNF-1
"""
import re
from typing import List, Tuple, Any

SECRET_PATTERNS = [
    (r"AZURE_SUBSCRIPTION_ID", "Azure Subscription ID"),
    (r"aws_access_key_id", "AWS Access Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "PEM Private Key block"),
    (r"password\s*=", "Password Assignment"),
    (r"token\s*[=:]", "Token Field"),
    (r"api[_-]?key", "API Key"),
    (r"secret[_-]?key", "Secret Key"),
    (r"private[_-]?key", "Private Key"),
    (r"api[_-]?token", "API Token"),
    (r"Bearer\s+[A-Za-z0-9\-_.]+", "Bearer Token"),
    (r"passwd", "Password Key"),
    (r"secret", "Generic Secret"),
]

def check_value_for_secrets(value: str) -> List[str]:
    """
    Chequea un texto contra patrones de secretos conocidos.
    Retorna la lista de tipos de secretos encontrados.
    """
    found = []
    for pattern, secret_type in SECRET_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            found.append(secret_type)
    return found

def scan_dict_for_secrets(data: Any, path: str = "") -> List[Tuple[str, str]]:
    """
    Escanea recursivamente una estructura de datos en busca de secretos.
    Retorna una lista de tuplas (ruta_de_clave, tipo_de_secreto).
    """
    findings = []
    
    if isinstance(data, str):
        types = check_value_for_secrets(data)
        for t in types:
            findings.append((path, t))
            
    elif isinstance(data, dict):
        for key, val in data.items():
            current_path = f"{path}.{key}" if path else key
            # Escanear el nombre de la clave en sí
            key_secrets = check_value_for_secrets(key)
            for ks in key_secrets:
                findings.append((current_path, f"{ks} (en nombre de clave)"))
            
            # Escanear el valor recursivamente
            findings.extend(scan_dict_for_secrets(val, current_path))
            
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{path}[{idx}]"
            findings.extend(scan_dict_for_secrets(item, current_path))
            
    return findings
