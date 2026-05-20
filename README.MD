
# H.U.N.N.I.G.A.N. - Universal Bridge

¡Bienvenido al repositorio de **H.U.N.N.I.G.A.N.**! Este proyecto es un ecosistema distribuido y multi-motor diseñado para permitir la creación de niveles y scripting dinámico en tiempo real utilizando lenguaje natural procesado por una Inteligencia Artificial local.

El sistema traduce instrucciones de usuario en español a comandos JSON estructurados que son administrados por un servidor central y consumidos por motores de videojuegos como **Godot, Unity y Unreal Engine**.

---

## 📋 Requisitos Previos

Asegúrate de tener instalados los siguientes componentes antes de iniciar la configuración:
1. **Python 3.10 o superior** (marcar la opción de agregar al PATH durante la instalación).
2. **Ollama** instalado y corriendo en tu sistema. Puedes descargarlo desde [ollama.com](https://ollama.com/).
3. **Godot Engine 4.x** (para la integración del cliente de Godot).

---

## 🛠️ Configuración del Entorno (Paso a Paso)

Sigue estos comandos de forma secuencial en tu terminal para clonar el proyecto, aislar las librerías y preparar el entorno de ejecución:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/santiaagoperez2812/Hunnigan-Universal-Bridge.git](https://github.com/santiaagoperez2812/Hunnigan-Universal-Bridge.git)
cd Hunnigan-Universal-Bridge

```

### 2. Crear y activar un Entorno Virtual (`venv`)

Es **obligatorio** el uso de un entorno virtual para que todos mantengamos las mismas versiones de las dependencias sin interferir con las configuraciones globales de tu equipo.

* **En Windows (PowerShell o CMD):**
```bash
python -m venv venv
.\venv\Scripts\activate

```


* **En Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate

```



*(Sabrás que el entorno está activo porque verás el prefijo `(venv)` al inicio de la línea de comandos).*

### 3. Instalar las dependencias del proyecto

Una vez que tengas el entorno virtual activado, instala todas las librerías necesarias ejecutando un solo comando:

```bash
pip install -r requirements.txt

```

> 📌 **Nota para el equipo:** El archivo `requirements.txt` incluye de forma automática las librerías clave utilizadas en el desarrollo: `fastapi`, `uvicorn`, `requests`, `customtkinter` y `ollama`.

### 4. Descargar el Modelo de Inteligencia Artificial

Para garantizar la generación de estructuras limpias y soporte multi-objeto, el agente utiliza el modelo especializado **`qwen2.5-coder:3b`** (~2.0 GB).

Con Ollama abierto en segundo plano, ejecuta en tu terminal:

```bash
ollama run qwen2.5-coder:3b

```

Una vez finalizada la descarga, puedes cerrar esa ventana o salir del prompt interactivo presionando `Ctrl + D`.

---

## 🎮 Configuración del Cliente en Godot Engine 4

Para que tu proyecto de Godot pueda conectarse al servidor central y ejecutar las acciones en caliente dentro del editor, debes instalar los scripts del ecosistema como un **EditorPlugin**:

1. Ve a la carpeta raíz de **tu propio proyecto de videojuegos en Godot**.
2. Crea una carpeta llamada `addons` (si no existe ya).
3. Dentro de `addons`, crea una subcarpeta llamada `hunnigan_link`.
4. Copia los siguientes archivos de este repositorio dentro de esa ruta (`https://github.com/santiaagoperez2812/Hunnigan_Link`):
* `hunnigan_link.gd`
* `plugin.cfg`
* `hunnigan_link.gd.uid`


5. Abre tu proyecto en Godot y dirígete al menú superior: **Proyecto -> Configuración del Proyecto -> pestañas de Plugins** (Project -> Project Settings -> Plugins).
6. Localiza el plugin **Hunnigan Link** y marca la casilla **"Activo"** (Enabled).

> 📡 **Verificación:** Si todo está bien configurado, verás en la pestaña **Output (Salida)** de Godot el mensaje: `[HUNNIGAN] Plugin activado, escuchando en http://127.0.0.1:8000/...`.

---

## 🚀 Guía de Ejecución Completa

Para probar todo el flujo, debes levantar los procesos en este orden estricto (recuerda activar el `venv` en cada terminal nueva de Python):

### Paso 1: Levantar el Servidor Central (FastAPI)

Ejecuta el backend que procesa, normaliza las coordenadas de transformación y administra las colas independientes de los motores:

```bash
python universal_bridge_server.py

```

El servidor quedará a la escucha en `http://127.0.0.1:8000`. Puedes explorar la documentación interactiva de la API entrando desde tu navegador a `http://127.0.0.1:8000/docs`.

### Paso 2: Ejecutar el Agente Gráfico (GUI)

En una **segunda terminal** independiente de Python, inicializa la interfaz de escritorio construida con CustomTkinter:

```bash
python ugb_agent.py

```

### Paso 3: Conectar el Motor

Abre el editor de Godot con el plugin activado. Ahora, cuando escribas una instrucción en el agente gráfico (ej: *"Genera un pasillo con un suelo BOX y tres obstáculos"*), selecciones **Godot** y presiones **"COMPILAR"**, el servidor retendrá el comando y el plugin de Godot lo instanciará de inmediato en tu escena activa.

---

## ⚙️ Configuración Personalizada Local (`config.json`)

Para evitar conflictos de rutas absolutas entre nuestros equipos, el archivo `config.json` está excluido en el `.gitignore`.

Si necesitas que el agente escanee carpetas locales de tus proyectos de Godot o Unity para reconocer tus assets existentes (`.tscn`, `.prefab`, etc.), crea un archivo llamado `config.json` en la raíz de este repositorio con la estructura correspondiente a tu sistema operativo:

```json
{
  "WINDOWS": {
    "PROJECT_PATH": "C:/Ruta/A/Tu/ProyectoGodot",
    "PATH_PROYECTO": "C:/Ruta/A/Tu/ProyectoUnity"
  },
  "LINUX": {
    "PROJECT_PATH": "/home/usuario/Proyectos/ProyectoGodot",
    "PATH_PROYECTO": "/home/usuario/Proyectos/ProyectoUnity"
  }
}

```

---

## 🔄 Flujo de Trabajo en Git (Evitar Errores de Push)

Es muy común que al intentar hacer un `git push origin main` recibas un error de rechazo (`[rejected] - fetch first`). Esto ocurre porque hay cambios en la nube que tú no tienes en tu máquina local.

Para resolverlo de forma segura sin romper tu código, sigue estos pasos:

1. **Guarda tus cambios locales:**
```bash
git add .
git commit -m "Descripción de tus avances"

```


2. **Trae e integra los cambios del servidor remoto:**
```bash
git pull origin main

```


*(Si hay algún conflicto de líneas, resuélvelo en tu editor, vuelve a hacer add/commit y continúa).*
3. **Sube tus cambios limpios:**
```bash
git push -u origin main

```

