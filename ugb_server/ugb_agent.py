# ugb_agent.py - Agente H.U.N.N.I.G.A.N. Universal (solo procesa y envía JSON)
import os
import json
import sys
import re
import threading
import requests
import customtkinter as ctk
import ollama
from typing import Any, List, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas solo para escanear assets existentes (contexto para la IA)
PROJECT_PATH = os.path.join(BASE_DIR, "godot_project")
PATH_PROYECTO = os.path.join(BASE_DIR, "MiProyectoGodot")

# Carga de configuración multiplataforma (solo para rutas de assets, nunca para escribir)
try:
    config_path = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as cf:
            _cfg = json.load(cf)
        entorno = "WINDOWS" if sys.platform.startswith("win") else "LINUX"
        if entorno in _cfg:
            cfg_entorno = _cfg[entorno]
            _proj = cfg_entorno.get("PROJECT_PATH")
            _path_proy = cfg_entorno.get("PATH_PROYECTO")
        else:
            _proj = _cfg.get("PROJECT_PATH")
            _path_proy = _cfg.get("PATH_PROYECTO")
        if _proj:
            PROJECT_PATH = _proj if os.path.isabs(_proj) else os.path.join(BASE_DIR, _proj)
        if _path_proy:
            PATH_PROYECTO = _path_proy if os.path.isabs(_path_proy) else os.path.join(BASE_DIR, _path_proy)
except Exception:
    pass

SUPPORTED_ENGINES = ["godot", "unity", "unreal"]
DEFAULT_ENGINE = "godot"

def scan_assets(engine: str = DEFAULT_ENGINE) -> Dict[str, List[str]]:
    """Escanea assets existentes (solo para contexto, no modifica nada)"""
    assets = {"2D": [], "3D": []}
    base_path = os.path.join(PROJECT_PATH, "assets")
    if not os.path.exists(base_path):
        return assets
    ext_map = {"godot": ".tscn", "unity": ".prefab", "unreal": ".uasset"}
    ext = ext_map.get(engine, ".tscn")
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith(ext):
                name = os.path.splitext(f)[0]
                assets["2D" if "2d" in root.lower() else "3D"].append(name)
    return assets

def safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except:
        return default

# Función de rescate (solo heurística, sin escritura)
def rescue_parse(raw: str) -> List[Dict]:
    data = {
        "engine": DEFAULT_ENGINE,
        "action": "SPAWN",
        "asset_data": {"name": "ObjetoGenerado", "type": "3D"},
        "transform": {"position": {"x": 0, "y": 0, "z": 0}},
        "scripting": {"content": ""}
    }
    low = raw.lower()
    if "esfera" in low or "bola" in low:
        data["asset_data"]["name"] = "Esfera"
    elif "cilindro" in low or "columna" in low:
        data["asset_data"]["name"] = "Cilindro"
    elif "capsula" in low:
        data["asset_data"]["name"] = "Capsula"
    elif "cubo" in low or "caja" in low:
        data["asset_data"]["name"] = "Cubo"
    # Extraer nombre entre comillas
    name_match = re.search(r"['\"]([^'\"]+)['\"]", raw)
    if name_match and len(name_match.group(1)) < 80:
        data["asset_data"]["name"] = name_match.group(1).strip()
    # Extraer posición
    nums = re.findall(r"-?\d+\.?\d*", raw)
    if len(nums) >= 3:
        data["transform"]["position"] = {"x": safe_float(nums[0]), "y": safe_float(nums[1]), "z": safe_float(nums[2])}
    # Extraer código GDScript
    if "func " in raw:
        idx = raw.find("func ")
        code = raw[idx:]
        code = re.sub(r"```[a-z]*\n?|```", "", code).strip()
        data["scripting"]["content"] = code.replace("\n", "\\n").replace('"', '\\"')
    return [data]

class HunniganAgent:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("H.U.N.N.I.G.A.N. INDUSTRIAL - Universal Agent")
        self.root.geometry("820x640")
        
        self.header = ctk.CTkLabel(self.root, text="H.U.N.N.I.G.A.N. Multi-Motor Agent", font=("Consolas", 20, "bold"))
        self.header.pack(pady=(12, 4))
        self.top_frame = ctk.CTkFrame(self.root)
        self.top_frame.pack(fill="x", padx=12, pady=(0, 8))
        self.engine_label = ctk.CTkLabel(self.top_frame, text="Motor destino:", width=120)
        self.engine_label.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="w")
        self.engine_selector = ctk.CTkOptionMenu(self.top_frame, values=SUPPORTED_ENGINES, command=self.on_engine_change)
        self.engine_selector.set(DEFAULT_ENGINE)
        self.engine_selector.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="w")
        self.status_label = ctk.CTkLabel(self.top_frame, text="Seleccione motor y escriba instrucción.", anchor="w")
        self.status_label.grid(row=0, column=2, padx=(10, 0), pady=6, sticky="ew")
        self.top_frame.grid_columnconfigure(2, weight=1)
        self.log_frame = ctk.CTkFrame(self.root)
        self.log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.log = ctk.CTkTextbox(self.log_frame, width=780, height=320, font=("Consolas", 11))
        self.log.pack(fill="both", expand=True, padx=8, pady=8)
        self.preview_label = ctk.CTkLabel(self.root, text="Vista previa JSON (enviado al servidor):", anchor="w")
        self.preview_label.pack(fill="x", padx=12)
        self.preview = ctk.CTkTextbox(self.root, width=780, height=150, font=("Consolas", 11), state="disabled")
        self.preview.pack(fill="both", expand=False, padx=12, pady=(4, 8))
        self.input_frame = ctk.CTkFrame(self.root)
        self.input_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.entry = ctk.CTkEntry(self.input_frame, width=600)
        self.entry.pack(side="left", padx=(0, 8), pady=8, fill="x", expand=True)
        self.btn = ctk.CTkButton(self.input_frame, text="COMPILAR", command=self.send)
        self.btn.pack(side="right", padx=(0, 8), pady=8)
        self.selected_engine = DEFAULT_ENGINE

    def on_engine_change(self, new_engine: str):
        self.selected_engine = new_engine
        self.status_label.configure(text=f"Motor: {new_engine}")
        self.log_message(f">> INFO: Motor cambiado a {new_engine}\n")

    def log_message(self, text: str):
        self.log.insert("end", text)
        self.log.see("end")

    def preview_json(self, content: str):
        self.preview.configure(state="normal")
        self.preview.delete("0.0", "end")
        self.preview.insert("end", content)
        self.preview.configure(state="disabled")

    def send(self):
        user_input = self.entry.get().strip()
        if not user_input:
            self.log_message(">> WARNING: Instrucción vacía.\n")
            return
        self.log_message(f">> USER ({self.selected_engine}): {user_input}\n")
        self.entry.delete(0, 'end')
        self.btn.configure(state="disabled", text="PROCESANDO...")
        threading.Thread(target=self.call_ai, args=(user_input,), daemon=True).start()

    def call_ai(self, user_input: str):
        self.preview_json("")
        self.log_message(">> INFO: Generando comando vía Ollama (qwen2.5-coder:3b)...\n")
        msg = ">> ERROR: Fallo desconocido.\n"
        try:
            assets = scan_assets(self.selected_engine)
            system_prompt = f"""Eres un traductor de lenguaje natural a JSON para el puente H.U.N.N.I.G.A.N.
            Motor actual: {self.selected_engine}
            Assets detectados: 2D={assets['2D']} 3D={assets['3D']}
            Reglas estrictas:
            - Devuelve SIEMPRE un array JSON válido, encerrado entre corchetes [ ... ]. No incluyas texto adicional fuera del array, ni explicaciones, ni bloques markdown.
            - Si el usuario solicita un escenario, mapa o un nivel completo, debes descomponer la solicitud y generar un objeto independiente para cada entidad u obstáculo dentro del mismo array JSON.
            - El campo "scripting.content" debe enviarse como una sola línea de texto, convirtiendo todos los saltos de línea físicos en caracteres escapados '\\n' y las comillas internas dobles en '\\"'.
            - No uses placeholders bajo ninguna circunstancia.
            - Si el usuario pide un cubo, pon "name":"Cubo". Esfera->"Esfera", Cilindro->"Cilindro", Cápsula->"Capsula".
            - Si se solicita lógica y no se provee código explícito, pon un script base funcional según el lenguaje: para godot "func _ready():\\n    pass"
            
            Ejemplo de salida esperada para un nivel o un objeto:
            [
                {{
                    "engine": "{self.selected_engine}",
                    "action": "SPAWN",
                    "asset_data": {{"name": "Suelo", "type": "3D"}},
                    "transform": {{"position": {{"x":0,"y":0,"z":0}}, "rotation": {{"x":0,"y":0,"z":0}}, "scale": {{"x":10,"y":1,"z":10}}}},
                    "scripting": {{"file_name": "script_suelo", "language": "gdscript", "content": "func _ready():\\n    pass"}}
                }}
            ]"""
            
            # Cambiado de 'tinyllama' a 'qwen2.5-coder:3b' para máxima precisión y soporte multi-objeto
            response = ollama.chat(model="qwen2.5-coder:3b", messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ])
            raw_output = response["message"]["content"].strip()
            
            # Limpiar bloques markdown generados por descuido por el LLM
            if raw_output.startswith("```json"):
                raw_output = raw_output[7:]
            if raw_output.startswith("```"):
                raw_output = raw_output[3:]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]
            raw_output = raw_output.strip()
            
            # Parsear JSON de forma robusta
            commands = None
            if raw_output.startswith("[") and raw_output.endswith("]"):
                try:
                    clean = re.sub(r"[\x00-\x1F\x7F]", "", raw_output)
                    commands = json.loads(clean)
                except:
                    commands = None
            if not commands:
                commands = rescue_parse(raw_output)
                
            # Normalizar y despachar al servidor
            if isinstance(commands, list) and len(commands) > 0:
                self.preview_json(json.dumps(commands, indent=2))
                resp = requests.post("http://127.0.0.1:8000/post_command", json=commands, timeout=10)
                if resp.status_code == 200:
                    msg = f">> OK: {len(commands)} comando(s) encolado(s) en servidor.\n"
                else:
                    msg = f">> ERROR: Servidor respondió {resp.status_code}: {resp.text}\n"
            else:
                msg = ">> ERROR: No se pudo generar ningún comando válido.\n"
        except Exception as e:
            msg = f">> ERROR: {str(e)}\n"
        finally:
            self.root.after(0, lambda: self.log_message(msg))
            self.root.after(0, lambda: self.btn.configure(state="normal", text="COMPILAR"))

if __name__ == "__main__":
    HunniganAgent().root.mainloop()