# 1. Instalar uv en tu usuario (toma unos 5 segundos)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Actualizar la ruta de la consola actual para que reconozca el comando uv
$env:Path = "C:\Users\Fl0c\.local\bin;$env:Path"
# 3. Descargar Python 3.12 automáticamente y crear el entorno .venv en tu carpeta actual
uv venv .venv --python 3.12

# 4. Activar el entorno virtual del proyecto
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.\.venv\Scripts\Activate.ps1



# 5. Instalar Playwright dentro de ese .venv y descargar Chromium
uv pip install playwright
playwright install chromium

# Activar virtual enviroment
To Activate the virtual enviroment with: .venv\Scripts\activate (powershell)

# Ejecutar programa
python scraper_tiktok.py khabi.lame
