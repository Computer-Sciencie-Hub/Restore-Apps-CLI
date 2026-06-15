# 📦 dotenv-manager: Setup Automatizado y Seguro de PC

`dotenv-manager` es una herramienta CLI robusta y modular escrita en Python 3.11+ que automatiza la captura, reporte y restauración declarativa del estado completo de una PC (aplicaciones instaladas, dependencias globales y archivos de configuración dotfiles) en minutos tras un formateo.

---

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias
Instala los paquetes requeridos por el sistema:
```bash
pip install -r requirements.txt
```
O de forma editable para poder invocarlo directamente:
```bash
pip install -e .
```

### 2. Capturar Estado Actual de la PC
Escanea el sistema operativo y genera un manifiesto descriptivo libre de bloatware:
```bash
python -m src.cli capture --output=my_setup.yaml --git-commit
```

### 3. Verificar Desvíos (Drift Detection)
Compara el PC actual contra un manifiesto y reporta inconsistencias o dotfiles alterados:
```bash
python -m src.cli verify my_setup.yaml
```

### 4. Generar Reporte HTML Categorizado
Compila una SPA interactiva y moderna para visualizar y filtrar tus aplicaciones:
```bash
python -m src.cli report --input=my_setup.yaml --output=my_setup_report.html
```

### 5. Restaurar Estado Completo
Planifica e instala de forma ordenada e idempotente las aplicaciones y dotfiles:
```bash
# Simular la restauración (Dry-Run)
python -m src.cli restore my_setup.yaml --dry-run

# Ejecutar restauración real
python -m src.cli restore my_setup.yaml
```

---

## 🔧 Comandos del CLI

El CLI de Click provee los siguientes comandos:

* `capture`: Escanea el host (Winget, Pip, Npm) y crea el manifiesto YAML. Cuenta con la opción `--git-commit` para versionarlo.
* `restore`: Lee el manifiesto, resuelve las dependencias en orden y restaura el PC. Opciones:
  * `--dry-run`: Solo simula.
  * `--only-tier=N`: Filtra para ejecutar solo paquetes de un tier específico (1, 2 o 3).
  * `--skip-tier=N`: Salta paquetes de un tier específico o superior.
  * `--force`: Sobrescribe dotfiles sin preguntar interactivamente.
  * `--no-backup`: Desactiva el respaldo automático de dotfiles previo al copiado.
* `verify`: Escanea el sistema actual y reporta desvíos (`OK`, `MODIFIED`, `MISSING`, `EXTRA`).
* `report`: Genera un reporte HTML autoportante interactivo con buscador y modo oscuro.
* `list`: Muestra la lista ordenada de aplicaciones con sus versiones y gestores.
* `instructions`: Genera o exporta una guía detallada (`AGENT_INSTRUCTIONS.md`) optimizada para que agentes de IA colaboren en la administración.
---

## 📁 Estructura del Workspace

```
Restore-Apps-CLI/
├── src/
│   ├── __init__.py
│   ├── __main__.py              ← Punto de entrada
│   ├── cli.py                   ← Definición de comandos de Click
│   ├── core/
│   │   ├── detector.py          ← Escaneo de sistema y dotfiles
│   │   ├── installer.py         ← Orquestación e idempotencia
│   │   ├── dependency_resolver.py ← Topological Sort e identificación de ciclos
│   │   ├── dotfile_manager.py   ← Copias y backups con sumas SHA-256
│   │   └── reporter.py          ← Generación de reporte HTML
│   ├── managers/
│   │   ├── base.py              ← Interfaz común
│   │   ├── winget.py            ← Winget parser y exclusión de bloatware de Windows 11
│   │   ├── pip.py / npm.py      ← Dependencias globales de desarrollo
│   │   └── apt.py / snap.py ...  ← Stubs compatibles con Linux/macOS
│   ├── models/
│   │   ├── package.py / manifest.py / system_info.py ← Modelos de datos
│   └── utils/
│       ├── crypto.py / shell.py / logger.py / validators.py ← Utilidades
├── AGENT_INSTRUCTIONS.md        ← Directrices de seguridad e instrucciones para IA
├── LICENSE                      ← Licencia MIT del proyecto
├── CHANGELOG.md                 ← Bitácora de cambios (excluida de Git)
├── requirements.txt             ← Dependencias del proyecto
└── setup.py                     ← Script de distribución
```

---

