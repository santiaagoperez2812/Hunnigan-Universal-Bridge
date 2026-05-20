# universal_bridge_server.py
from fastapi import FastAPI, HTTPException, Request, Query
from typing import List, Dict, Any, Optional
import uvicorn
import json
import re

app = FastAPI(title="H.U.N.N.I.G.A.N. Universal Bridge Server")

ALLOWED_ENGINES = {"godot", "unity", "unreal"}
ALLOWED_ACTIONS = {"SPAWN", "WRITE_CODE", "DELETE"}
command_queues: Dict[str, List[Dict[str, Any]]] = {e: [] for e in ALLOWED_ENGINES}

def normalize_command(raw_cmd: Any) -> Dict[str, Any]:
    if not isinstance(raw_cmd, dict):
        raise ValueError("Comando debe ser objeto JSON")
    engine = raw_cmd.get("engine", "godot").strip().lower()
    if engine not in ALLOWED_ENGINES:
        engine = "godot"
    action = raw_cmd.get("action", "SPAWN").strip().upper()
    if action not in ALLOWED_ACTIONS:
        action = "SPAWN"
        
    # asset_data
    asset = raw_cmd.get("asset_data", {})
    if not isinstance(asset, dict):
        asset = {}
    name = str(asset.get("name", "generic_asset")).strip() or "generic_asset"
    typ = str(asset.get("type", "3D")).strip().upper()
    if typ not in {"2D", "3D"}:
        typ = "3D"
    ext_map = {"godot": ".tscn", "unity": ".prefab", "unreal": ".uasset"}
    file_ext = asset.get("file_extension", "").strip()
    if not file_ext:
        file_ext = ext_map.get(engine, ".tscn")
        
    # transform
    trans = raw_cmd.get("transform", {})
    if not isinstance(trans, dict):
        trans = {}
    pos = trans.get("position", {})
    if isinstance(pos, list):
        pos = {"x": float(pos[0]) if len(pos) > 0 else 0.0,
               "y": float(pos[1]) if len(pos) > 1 else 0.0,
               "z": float(pos[2]) if len(pos) > 2 else 0.0}
    elif not isinstance(pos, dict):
        pos = {}
    rot = trans.get("rotation", {}) or {}
    scale = trans.get("scale", {}) or {}
    
    def f(v, default=0.0):
        try:
            return float(v)
        except:
            return default
            
    position = {"x": f(pos.get("x")), "y": f(pos.get("y")), "z": f(pos.get("z"))}
    rotation = {"x": f(rot.get("x")), "y": f(rot.get("y")), "z": f(rot.get("z"))}
    scale_vec = {"x": f(scale.get("x"), 1.0), "y": f(scale.get("y"), 1.0), "z": f(scale.get("z"), 1.0)}
    
    # scripting
    script = raw_cmd.get("scripting", {})
    if not isinstance(script, dict):
        script = {}
    script_name = str(script.get("file_name", "script")).strip() or "script"
    lang = str(script.get("language", "gdscript")).strip().lower()
    if lang not in {"gdscript", "csharp", "cpp"}:
        lang = "gdscript"
        
    # El contenido ya viene escapado del agente, lo desescapamos para almacenarlo raw en el servidor.
    content_raw = str(script.get("content", "")).strip()
    content_raw = content_raw.replace("\\n", "\n")
    
    return {
        "engine": engine,
        "action": action,
        "asset_data": {"name": name, "type": typ, "file_extension": file_ext},
        "transform": {"position": position, "rotation": rotation, "scale": scale_vec},
        "scripting": {"file_name": script_name, "language": lang, "content": content_raw}
    }

@app.post("/post_command")
async def post_command(request: Request):
    try:
        body = await request.body()
        text = body.decode("utf-8")
        # Limpieza ligera de caracteres de control no válidos
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        payload = json.loads(text)
        commands = payload if isinstance(payload, list) else [payload]
        stored = 0
        for cmd in commands:
            norm = normalize_command(cmd)
            command_queues[norm["engine"]].append(norm)
            stored += 1
            print(f"[SERVER] Comando encolado para {norm['engine']}: {norm['asset_data']['name']}")
        return {"status": "ok", "queued": stored, "queues": {k: len(v) for k, v in command_queues.items()}}
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"JSON inválido: {e}")
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/get_pending_commands")
async def get_pending_commands(engine: Optional[str] = Query(None, description="godot, unity, unreal")):
    if engine:
        engine = engine.strip().lower()
        if engine not in ALLOWED_ENGINES:
            raise HTTPException(400, f"Motor desconocido: {engine}")
        pending = list(command_queues[engine])
        command_queues[engine].clear()
        return pending
        
    # Sin parámetro: devolver todos los comandos de todas las colas
    all_pending = []
    for e in ALLOWED_ENGINES:
        all_pending.extend(command_queues[e])
        command_queues[e].clear()
    return all_pending

@app.get("/queue_status")
async def queue_status():
    return {e: len(command_queues[e]) for e in ALLOWED_ENGINES}

@app.get("/")
async def root():
    return {"message": "H.U.N.N.I.G.A.N. Bridge activo", "queues": {k: len(v) for k, v in command_queues.items()}}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)