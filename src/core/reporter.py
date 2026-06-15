"""
Generador de Reportes HTML Interactivos - PRD §📋
"""
import os
import json
from typing import List, Dict
from src.models.manifest import Manifest
from src.models.package import Package

class HTMLReporter:
    """Clasifica los paquetes de un manifiesto y genera un reporte HTML premium."""

    CATEGORIES = {
        "Desarrollo y Programación": {"icon": "code", "color": "indigo", "desc": "IDEs, compiladores, terminales, bases de datos y herramientas de desarrollo."},
        "Productividad y Oficina": {"icon": "briefcase", "color": "emerald", "desc": "Gestores de notas, herramientas de oficina, chats de equipo y organizadores."},
        "Diseño y Creatividad": {"icon": "palette", "color": "purple", "desc": "Edición de audio, video, diseño vectorial y procesamiento de imagen."},
        "Entretenimiento y Juegos": {"icon": "gamepad-2", "color": "rose", "desc": "Videojuegos, plataformas de distribución y reproductores multimedia."},
        "Utilidades y Sistema": {"icon": "cpu", "color": "amber", "desc": "Controladores de hardware, emuladores, virtualización y herramientas del SO."},
        "Paquetes de Python": {"icon": "binary", "color": "blue", "desc": "Librerías y dependencias de Python instaladas en el entorno local (pip)."},
        "Paquetes de Node.js (npm)": {"icon": "blocks", "color": "teal", "desc": "Módulos y herramientas globales de Node.js (npm)."},
        "Otros": {"icon": "package", "color": "slate", "desc": "Aplicaciones y dependencias que no coinciden con las categorías anteriores."}
    }

    @staticmethod
    def categorize_package(pkg: Package) -> str:
        """Determina el área de una aplicación según su nombre, ID o descripción."""
        pkg_id_lower = pkg.name.lower()
        friendly_name_lower = pkg.name.lower()
        if pkg.manager == "winget" and pkg.description.startswith("App: "):
            friendly_name_lower = pkg.description[5:].lower()

        # DEVELOPMENT
        dev_keywords = [
            "visualstudio", "jetbrains", "intellij", "cursor", "unity", "git", "cmake", 
            "python", "node", "nmap", "ninja", "github", "oracle.jdk", "jdk", "jre", "dbeaver", 
            "docker", "mysql", "sqlserver", "ssms", "playit", "antigravity", "staruml", 
            "daemontools", "postman", "sublime", "notepad++", "anaconda", "copilot", "codex", 
            "rust", "go", "gcc", "clang", "llvm", "mingw", "maven", "gradle", "vss writer"
        ]
        # PRODUCTIVITY
        prod_keywords = [
            "obsidian", "notion", "milanote", "excalidraw", "claude", "office", "powerbi", 
            "zoom", "whatsapp", "discord", "slack", "teams", "m365", "outlook", "word", 
            "excel", "powerpoint", "onenote", "todoist", "anydesk", "trello", "skype", "adobe", 
            "acrobat", "foxit", "copilot", "keep", "evernote", "notion", "google ai studio"
        ]
        # DESIGN & MULTIMEDIA
        design_keywords = [
            "affinity", "canva", "davinci", "nikon", "nx studio", "blackmagic", "photoshop", 
            "illustrator", "premiere", "gimp", "inkscape", "blender", "audacity", "vlc", 
            "handbrake", "obs-studio", "soundrecorder", "camera", "cámara", "fotos", "photos", 
            "paint", "reloj de windows", "windowsalarms", "alarms", "reloj"
        ]
        # GAMING & ENTERTAINMENT
        game_keywords = [
            "steam", "minecraft", "roblox", "spotify", "netflix", "disney", "amazonvideo", 
            "primevideo", "valve", "balatro", "roulette", "zomboid", "valley", "poker", 
            "strike", "epicgames", "ea.desktop", "riot", "valorant", "vanguard", "twitch", "gaming"
        ]
        # SYSTEM UTILITIES
        util_keywords = [
            "winrar", "virtualbox", "ollama", "npcap", "ngenuity", "acuity", "finereader", 
            "driver", "amd", "intel", "nvidia", "realtek", "vcredist", "vclibs", "directx", 
            "controller", "experiencepack", "widgetsplatform", "shellextension", "help viewer", 
            "visor de ayuda", "paquete de idioma", "languagepack"
        ]

        # Comprobar contra el ID y el nombre amigable
        for kw in dev_keywords:
            if kw in pkg_id_lower or kw in friendly_name_lower:
                return "Desarrollo y Programación"
                
        for kw in prod_keywords:
            if kw in pkg_id_lower or kw in friendly_name_lower:
                return "Productividad y Oficina"
                
        for kw in design_keywords:
            if kw in pkg_id_lower or kw in friendly_name_lower:
                return "Diseño y Creatividad"
                
        for kw in game_keywords:
            if kw in pkg_id_lower or kw in friendly_name_lower:
                return "Entretenimiento y Juegos"
                
        for kw in util_keywords:
            if kw in pkg_id_lower or kw in friendly_name_lower:
                return "Utilidades y Sistema"

        if pkg.manager == "pip":
            return "Paquetes de Python"
            
        if pkg.manager == "npm":
            return "Paquetes de Node.js (npm)"

        return "Otros"

    def generate_report(self, manifest: Manifest, output_path: str) -> bool:
        """Categoriza las aplicaciones y genera el archivo HTML autocontenido."""
        # Agrupar paquetes
        grouped_packages: Dict[str, List[dict]] = {cat: [] for cat in self.CATEGORIES}
        
        winget_count = 0
        pip_count = 0
        npm_count = 0
        
        for pkg in manifest.packages:
            category = self.categorize_package(pkg)
            if category not in grouped_packages:
                category = "Otros"
                
            friendly_name = pkg.name
            if pkg.manager == "winget" and pkg.description.startswith("App: "):
                friendly_name = pkg.description[5:]
                
            # Contador por gestor
            if pkg.manager == "winget":
                winget_count += 1
            elif pkg.manager == "pip":
                pip_count += 1
            elif pkg.manager == "npm":
                npm_count += 1

            grouped_packages[category].append({
                "id": pkg.name,
                "friendly_name": friendly_name,
                "manager": pkg.manager,
                "version": pkg.version,
                "repository": pkg.repository if pkg.repository else "local",
                "description": pkg.description
            })

        # Ordenar cada categoría alfabéticamente por nombre amigable
        for cat in grouped_packages:
            grouped_packages[cat].sort(key=lambda p: p["friendly_name"].lower())

        # Metadata del reporte
        metadata = manifest.metadata or {}
        sys_info = {
            "os": metadata.get("os", "Desconocido").upper(),
            "arch": metadata.get("arch", "Desconocido"),
            "hostname": metadata.get("hostname", "Desconocido"),
            "user": metadata.get("user", "Desconocido"),
            "timestamp": metadata.get("timestamp", "Desconocido"),
            "total_packages": len(manifest.packages),
            "winget_count": winget_count,
            "pip_count": pip_count,
            "npm_count": npm_count
        }

        # Generar JSON estructurado para inyectar en JS
        data_json = json.dumps({
            "sys_info": sys_info,
            "categories": self.CATEGORIES,
            "packages": grouped_packages
        }, ensure_ascii=False)

        # Cargar plantilla
        html_content = self._get_template_html(data_json)
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception:
            return False

    def _get_template_html(self, data_json: str) -> str:
        """Retorna el contenido de la plantilla HTML con el JSON inyectado."""
        return f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dotenv-manager | Reporte de Aplicaciones</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                        title: ['Outfit', 'sans-serif'],
                    }},
                }}
            }}
        }}
    </script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .glass {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .light .glass {{
            background: rgba(0, 0, 0, 0.01);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.05);
        }}
        .card-glow:hover {{
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
        }}
        .light .card-glow:hover {{
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
            border-color: rgba(99, 102, 241, 0.3);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body class="bg-[#0b0f19] text-slate-100 font-sans min-h-screen transition-colors duration-300 light:bg-slate-50 light:text-slate-800">
    <!-- Contenedor Principal -->
    <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        
        <!-- Header -->
        <header class="flex flex-col md:flex-row md:items-center md:justify-between pb-8 border-b border-slate-800 dark:border-slate-800 light:border-slate-200">
            <div>
                <div class="flex items-center space-x-3">
                    <div class="p-2.5 bg-indigo-600 rounded-xl text-white shadow-lg shadow-indigo-600/30">
                        <i data-lucide="check-square" class="w-6 h-6"></i>
                    </div>
                    <h1 class="text-3xl font-extrabold font-title tracking-tight text-white light:text-slate-900">
                        dotenv-manager <span class="text-indigo-400 font-light">Inventory</span>
                    </h1>
                </div>
                <p class="mt-2 text-sm text-slate-400 light:text-slate-500">
                    Detección y clasificación automatizada del estado local de tu PC
                </p>
            </div>
            
            <!-- Controles -->
            <div class="mt-4 md:mt-0 flex items-center space-x-4">
                <!-- Toggle Dark/Light Mode -->
                <button id="theme-toggle" class="p-2.5 rounded-xl border border-slate-800 bg-[#0e1322] text-slate-400 hover:text-white hover:border-slate-700 light:bg-white light:border-slate-200 light:text-slate-600 light:hover:bg-slate-50 transition-all">
                    <i id="theme-toggle-dark-icon" data-lucide="sun" class="w-5 h-5 hidden"></i>
                    <i id="theme-toggle-light-icon" data-lucide="moon" class="w-5 h-5"></i>
                </button>
            </div>
        </header>

        <!-- Stats Dashboard -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4 py-8">
            <div class="glass p-5 rounded-2xl border border-slate-800 light:bg-white light:border-slate-200">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Aplicaciones</span>
                    <span class="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400"><i data-lucide="box" class="w-4 h-4"></i></span>
                </div>
                <div class="mt-4 flex items-baseline">
                    <span class="text-3xl font-bold font-title text-white light:text-slate-900" id="stat-total">0</span>
                </div>
            </div>
            
            <div class="glass p-5 rounded-2xl border border-slate-800 light:bg-white light:border-slate-200">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Paquetes winget</span>
                    <span class="p-1.5 bg-sky-500/10 rounded-lg text-sky-400"><i data-lucide="terminal" class="w-4 h-4"></i></span>
                </div>
                <div class="mt-4 flex items-baseline">
                    <span class="text-3xl font-bold font-title text-white light:text-slate-900" id="stat-winget">0</span>
                </div>
            </div>

            <div class="glass p-5 rounded-2xl border border-slate-800 light:bg-white light:border-slate-200">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Entorno Python (pip)</span>
                    <span class="p-1.5 bg-blue-500/10 rounded-lg text-blue-400"><i data-lucide="binary" class="w-4 h-4"></i></span>
                </div>
                <div class="mt-4 flex items-baseline">
                    <span class="text-3xl font-bold font-title text-white light:text-slate-900" id="stat-pip">0</span>
                </div>
            </div>

            <div class="glass p-5 rounded-2xl border border-slate-800 light:bg-white light:border-slate-200">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Node.js Global (npm)</span>
                    <span class="p-1.5 bg-teal-500/10 rounded-lg text-teal-400"><i data-lucide="blocks" class="w-4 h-4"></i></span>
                </div>
                <div class="mt-4 flex items-baseline">
                    <span class="text-3xl font-bold font-title text-white light:text-slate-900" id="stat-npm">0</span>
                </div>
            </div>
        </section>

        <!-- System Metadata & Search -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-8">
            <!-- Info del Sistema -->
            <div class="lg:col-span-2 glass p-5 rounded-2xl border border-slate-800 light:bg-white light:border-slate-200 flex flex-wrap gap-y-4 gap-x-6 text-sm items-center">
                <div>
                    <span class="block text-slate-400 text-xs font-medium uppercase tracking-wider">Sistema Operativo</span>
                    <span class="text-white font-semibold font-title light:text-slate-900 flex items-center mt-0.5">
                        <i data-lucide="monitor" class="w-4 h-4 mr-1.5 text-indigo-400"></i>
                        <span id="sys-os">-</span>
                    </span>
                </div>
                <div class="h-8 w-[1px] bg-slate-800 light:bg-slate-200 hidden sm:block"></div>
                <div>
                    <span class="block text-slate-400 text-xs font-medium uppercase tracking-wider">Hostname</span>
                    <span class="text-white font-semibold light:text-slate-900 flex items-center mt-0.5" id="sys-host">-</span>
                </div>
                <div class="h-8 w-[1px] bg-slate-800 light:bg-slate-200 hidden sm:block"></div>
                <div>
                    <span class="block text-slate-400 text-xs font-medium uppercase tracking-wider">Usuario</span>
                    <span class="text-white font-semibold light:text-slate-900 flex items-center mt-0.5">
                        <i data-lucide="user" class="w-4 h-4 mr-1.5 text-emerald-400"></i>
                        <span id="sys-user">-</span>
                    </span>
                </div>
                <div class="h-8 w-[1px] bg-slate-800 light:bg-slate-200 hidden sm:block"></div>
                <div>
                    <span class="block text-slate-400 text-xs font-medium uppercase tracking-wider">Última Captura</span>
                    <span class="text-white font-semibold light:text-slate-900 flex items-center mt-0.5" id="sys-time">-</span>
                </div>
            </div>

            <!-- Búsqueda -->
            <div class="relative flex items-center">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <i data-lucide="search" class="w-5 h-5"></i>
                </div>
                <input type="text" id="search-input" placeholder="Buscar aplicaciones..." class="block w-full pl-11 pr-4 py-3 bg-[#0e1322] border border-slate-800 rounded-2xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent light:bg-white light:border-slate-200 light:text-slate-800 light:placeholder-slate-400 transition-all">
            </div>
        </section>

        <!-- Categories Sidebar & Cards Grid -->
        <main class="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <!-- Navegación de Categorías -->
            <aside class="space-y-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 px-3 mb-3">Filtrar por Área</h3>
                <button onclick="filterCategory('all')" id="btn-cat-all" class="w-full text-left px-4 py-3 rounded-xl flex items-center justify-between text-sm font-semibold transition-all bg-indigo-600/15 border border-indigo-600/30 text-indigo-400">
                    <span class="flex items-center"><i data-lucide="layout-grid" class="w-4 h-4 mr-2.5"></i>Todas las áreas</span>
                    <span class="px-2 py-0.5 bg-indigo-600/20 text-indigo-300 text-xs rounded-full font-bold" id="badge-cat-all">0</span>
                </button>
                <div id="category-sidebar-list" class="space-y-1">
                    <!-- Dinámico -->
                </div>
            </aside>

            <!-- Grid Principal de Contenido -->
            <div class="lg:col-span-3 space-y-10" id="categories-container">
                <!-- Secciones Dinámicas -->
            </div>
        </main>

        <!-- Footer -->
        <footer class="mt-20 pt-8 border-t border-slate-800 light:border-slate-200 text-center text-xs text-slate-500">
            <p>Generado con ❤️ por <strong>dotenv-manager</strong>. Licencia MIT.</p>
        </footer>
    </div>

    <!-- Script de Datos e Interacción -->
    <script>
        // Datos inyectados por Python
        const reportData = {data_json};

        // Estado global de filtros
        let activeCategory = 'all';
        let searchQuery = '';

        // Mapeo de colores Tailwind
        const colorMap = {{
            indigo: {{ bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/20', hover: 'hover:border-indigo-500/40', accent: 'bg-indigo-600' }},
            emerald: {{ bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', hover: 'hover:border-emerald-500/40', accent: 'bg-emerald-600' }},
            purple: {{ bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20', hover: 'hover:border-purple-500/40', accent: 'bg-purple-600' }},
            rose: {{ bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', hover: 'hover:border-rose-500/40', accent: 'bg-rose-600' }},
            amber: {{ bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', hover: 'hover:border-amber-500/40', accent: 'bg-amber-600' }},
            blue: {{ bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', hover: 'hover:border-blue-500/40', accent: 'bg-blue-600' }},
            teal: {{ bg: 'bg-teal-500/10', text: 'text-teal-400', border: 'border-teal-500/20', hover: 'hover:border-teal-500/40', accent: 'bg-teal-600' }},
            slate: {{ bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20', hover: 'hover:border-slate-500/40', accent: 'bg-slate-600' }}
        }};

        const managerColors = {{
            winget: 'bg-sky-500/10 text-sky-400 border border-sky-500/20',
            pip: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
            npm: 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
        }};

        // Inicialización
        document.addEventListener('DOMContentLoaded', () => {{
            setupMetadata();
            renderSidebar();
            renderContent();
            setupSearch();
            setupTheme();
            lucide.createIcons();
        }});

        function setupMetadata() {{
            const sys = reportData.sys_info;
            document.getElementById('stat-total').innerText = sys.total_packages;
            document.getElementById('stat-winget').innerText = sys.winget_count;
            document.getElementById('stat-pip').innerText = sys.pip_count;
            document.getElementById('stat-npm').innerText = sys.npm_count;

            document.getElementById('sys-os').innerText = sys.os + ' (' + sys.arch + ')';
            document.getElementById('sys-host').innerText = sys.hostname;
            document.getElementById('sys-user').innerText = sys.user;
            
            // Formatear Fecha
            try {{
                const date = new Date(sys.timestamp);
                document.getElementById('sys-time').innerText = date.toLocaleString('es-ES');
            }} catch(e) {{
                document.getElementById('sys-time').innerText = sys.timestamp;
            }}

            document.getElementById('badge-cat-all').innerText = sys.total_packages;
        }}

        function renderSidebar() {{
            const list = document.getElementById('category-sidebar-list');
            list.innerHTML = '';
            
            for (const [name, meta] of Object.entries(reportData.categories)) {{
                const count = reportData.packages[name] ? reportData.packages[name].length : 0;
                
                const btn = document.createElement('button');
                btn.id = `btn-cat-${{name}}`;
                btn.onclick = () => filterCategory(name);
                btn.className = `w-full text-left px-4 py-3 rounded-xl flex items-center justify-between text-sm font-semibold transition-all border border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 light:hover:bg-slate-200/50 light:hover:text-slate-900`;
                
                const textSpan = document.createElement('span');
                textSpan.className = 'flex items-center';
                
                const icon = document.createElement('i');
                icon.setAttribute('data-lucide', meta.icon);
                icon.className = `w-4 h-4 mr-2.5 text-${{meta.color}}-400`;
                
                textSpan.appendChild(icon);
                textSpan.appendChild(document.createTextNode(name));
                
                const countBadge = document.createElement('span');
                countBadge.className = `px-2 py-0.5 bg-${{meta.color}}-500/10 text-${{meta.color}}-400 border border-${{meta.color}}-500/20 text-xs rounded-full font-bold`;
                countBadge.innerText = count;
                
                btn.appendChild(textSpan);
                btn.appendChild(countBadge);
                list.appendChild(btn);
            }}
        }}

        function renderContent() {{
            const container = document.getElementById('categories-container');
            container.innerHTML = '';
            
            for (const [catName, meta] of Object.entries(reportData.categories)) {{
                const pkgs = reportData.packages[catName] || [];
                const colors = colorMap[meta.color] || colorMap.slate;
                
                // Filtrar según query y categoría activa
                const filteredPkgs = pkgs.filter(pkg => {{
                    const matchesSearch = pkg.friendly_name.toLowerCase().includes(searchQuery) ||
                                          pkg.id.toLowerCase().includes(searchQuery) ||
                                          pkg.description.toLowerCase().includes(searchQuery);
                    
                    const matchesCategory = activeCategory === 'all' || activeCategory === catName;
                    return matchesSearch && matchesCategory;
                }});

                if (filteredPkgs.length === 0) continue;

                // Crear Sección de la Categoría
                const section = document.createElement('section');
                section.className = 'space-y-4';
                
                const header = document.createElement('div');
                header.className = 'flex items-center space-x-3 pb-2 border-b border-slate-800 light:border-slate-200';
                
                const iconBox = document.createElement('div');
                iconBox.className = `p-2 ${{colors.bg}} rounded-xl ${{colors.text}} border ${{colors.border}}`;
                iconBox.innerHTML = `<i data-lucide="${{meta.icon}}" class="w-5 h-5"></i>`;
                
                const titleInfo = document.createElement('div');
                const title = document.createElement('h2');
                title.className = 'text-xl font-bold font-title text-white light:text-slate-900';
                title.innerText = catName;
                
                const desc = document.createElement('p');
                desc.className = 'text-xs text-slate-400 light:text-slate-500';
                desc.innerText = meta.desc;

                titleInfo.appendChild(title);
                titleInfo.appendChild(desc);
                header.appendChild(iconBox);
                header.appendChild(titleInfo);
                section.appendChild(header);

                // Grid de Apps
                const grid = document.createElement('div');
                grid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';
                
                filteredPkgs.forEach(pkg => {{
                    const card = document.createElement('div');
                    card.className = `glass p-4 rounded-xl border border-slate-800 light:bg-white light:border-slate-200 card-glow transition-all duration-300 flex flex-col justify-between`;
                    
                    const topDiv = document.createElement('div');
                    const titleRow = document.createElement('div');
                    titleRow.className = 'flex items-start justify-between gap-2';
                    
                    const appTitle = document.createElement('h4');
                    appTitle.className = 'font-bold text-sm text-white light:text-slate-900 truncate';
                    appTitle.title = pkg.friendly_name;
                    appTitle.innerText = pkg.friendly_name;
                    
                    const managerBadge = document.createElement('span');
                    managerBadge.className = `px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${{managerColors[pkg.manager] || 'bg-slate-700/20 text-slate-400'}}`;
                    managerBadge.innerText = pkg.manager;
                    
                    titleRow.appendChild(appTitle);
                    titleRow.appendChild(managerBadge);
                    topDiv.appendChild(titleRow);

                    if (pkg.id && pkg.id !== pkg.friendly_name) {{
                        const appId = document.createElement('span');
                        appId.className = 'block text-[10px] text-slate-500 font-mono mt-0.5 truncate';
                        appId.innerText = pkg.id;
                        topDiv.appendChild(appId);
                    }}

                    const botRow = document.createElement('div');
                    botRow.className = 'flex items-center justify-between mt-4 text-xs';
                    
                    const versionBox = document.createElement('span');
                    versionBox.className = 'text-slate-400 light:text-slate-500 font-semibold';
                    versionBox.innerText = 'v' + pkg.version;
                    
                    const repoBox = document.createElement('span');
                    if (pkg.repository === 'local') {{
                        repoBox.className = 'text-amber-500/80 bg-amber-500/10 px-1.5 py-0.5 rounded text-[10px] font-semibold border border-amber-500/25 flex items-center';
                        repoBox.innerHTML = '<i data-lucide="alert-triangle" class="w-3 h-3 mr-1"></i>local';
                    }} else {{
                        repoBox.className = 'text-slate-500 bg-slate-500/5 px-1.5 py-0.5 rounded text-[10px] font-semibold border border-slate-800 light:border-slate-200';
                        repoBox.innerText = pkg.repository;
                    }}

                    botRow.appendChild(versionBox);
                    botRow.appendChild(repoBox);
                    
                    card.appendChild(topDiv);
                    card.appendChild(botRow);
                    grid.appendChild(card);
                }});

                section.appendChild(grid);
                container.appendChild(section);
            }}
            
            lucide.createIcons();
        }}

        function filterCategory(catName) {{
            activeCategory = catName;
            
            // Actualizar botones de navegación
            const allBtn = document.getElementById('btn-cat-all');
            allBtn.className = `w-full text-left px-4 py-3 rounded-xl flex items-center justify-between text-sm font-semibold transition-all border ${{catName === 'all' ? 'bg-indigo-600/15 border-indigo-600/30 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 light:hover:bg-slate-200/50 light:hover:text-slate-900'}}`;
            
            for (const name of Object.keys(reportData.categories)) {{
                const btn = document.getElementById(`btn-cat-${{name}}`);
                const meta = reportData.categories[name];
                
                if (btn) {{
                    if (catName === name) {{
                        btn.className = `w-full text-left px-4 py-3 rounded-xl flex items-center justify-between text-sm font-semibold transition-all border bg-${{meta.color}}-500/15 border-${{meta.color}}-500/30 text-${{meta.color}}-400`;
                    }} else {{
                        btn.className = `w-full text-left px-4 py-3 rounded-xl flex items-center justify-between text-sm font-semibold transition-all border border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 light:hover:bg-slate-200/50 light:hover:text-slate-900`;
                    }}
                }}
            }}
            
            renderContent();
        }}

        function setupSearch() {{
            const input = document.getElementById('search-input');
            input.addEventListener('input', (e) => {{
                searchQuery = e.target.value.toLowerCase().strip ? e.target.value.toLowerCase().trim() : e.target.value.toLowerCase();
                renderContent();
            }});
        }}

        function setupTheme() {{
            const themeToggleBtn = document.getElementById('theme-toggle');
            const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
            const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

            // Cargar preferencia guardada
            if (localStorage.getItem('color-theme') === 'light' || (!('color-theme' in localStorage) && !window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
                document.documentElement.classList.remove('dark');
                document.documentElement.classList.add('light');
                themeToggleDarkIcon.classList.remove('hidden');
                themeToggleLightIcon.classList.add('hidden');
            }} else {{
                document.documentElement.classList.add('dark');
                document.documentElement.classList.remove('light');
                themeToggleDarkIcon.classList.add('hidden');
                themeToggleLightIcon.classList.remove('hidden');
            }}

            themeToggleBtn.addEventListener('click', () => {{
                // Alternar iconos
                themeToggleDarkIcon.classList.toggle('hidden');
                themeToggleLightIcon.classList.toggle('hidden');

                // Si está en modo oscuro
                if (document.documentElement.classList.contains('dark')) {{
                    document.documentElement.classList.remove('dark');
                    document.documentElement.classList.add('light');
                    localStorage.setItem('color-theme', 'light');
                }} else {{
                    document.documentElement.classList.add('dark');
                    document.documentElement.classList.remove('light');
                    localStorage.setItem('color-theme', 'dark');
                }}
            }});
        }}
    </script>
</body>
</html>
"""
