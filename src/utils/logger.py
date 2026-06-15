"""
Módulo de Logging centralizado - PRD §RT-1
"""
import logging
from colorama import init, Fore, Style

# Inicializar colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Formateador de logs para colorear mensajes según el nivel"""
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "%(levelname)s: %(message)s" + Style.RESET_ALL,
        logging.INFO: "%(message)s",
        logging.WARNING: Fore.YELLOW + "⚠️  %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "❌ %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + "🚨 %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name: str = "dotenv-manager", level: int = logging.INFO) -> logging.Logger:
    """Configura y retorna un logger formateado"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)
        
    return logger

# Instancia global del logger
logger = setup_logger()
