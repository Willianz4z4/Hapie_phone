import os
import sys
import glob
import time
import json
import sqlite3
import subprocess
import urllib.request
from datetime import datetime

LOOP_INTERVAL = 10
MIN_TOKEN_LENGTH = 500

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

def limpar_zumbis():
    print("[🧹] Limpando processos zumbis, travas e scripts temporários...")
    try:
        os.system("pkill -f 'picture_profile' > /dev/null 2>&1")
        os.system("proot-distro login ubuntu -- pkill -f 'picture_profile' > /dev/null 2>&1")
    except Exception: pass

    try:
        data_dir = get_data_dir()
        for lock in glob.glob(os.path.join(data_dir, ".lock_*")):
            try: os.remove(lock)
            except: pass
        for tmp_py in glob.glob(os.path.join(data_dir, ".run_profile_*.py")):
            try: os.remove(tmp_py)
            except: pass
    except Exception: pass

def get_data_dir():
    data_dir = os.path.join(PROJECT_ROOT, "Data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def verificar_ou_criar_tarefas_pendentes():
    data_dir = get_data_dir()
    tasks_file = os.path.join(data_dir, "scheduled_tasks.json")
    if not os.path.exists(tasks_file):
        try:
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump({"roblox_radar": "Pending"}, f, indent=4, ensure_ascii=False)
            print("[📋] Arquivo universal de rotinas criado.")
        except: pass

def load_saved_tokens():
    json_path = os.path.join(get_data_dir(), "Roblox_token.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_to_json(dados_salvos):
    json_path = os.path.join(get_data_dir(), "Roblox_token.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados_salvos, f, indent=4, ensure_ascii=False)

def get_roblox_username(token):
    try:
        req = urllib.request.Request(
            "https://users.roblox.com/v1/users/authenticated",
            headers={"Cookie": f".ROBLOSECURITY={token}", "User-Agent": "Roblox/WinInet"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode()).get("name")
    except: return None

def extract_active_token(pkg):
    """Puxa APENAS o token atual (Focus) que está no cookie do WebView"""
    locais_db = [
        f"/data/data/{pkg}/app_webview/Default/Cookies",
        f"/data/data/{pkg}/app_webview/Default/Network/Cookies"
    ]
    
    for db_origem in locais_db:
        db_temp = f"/data/data/com.termux/files/home/temp_cookie_{pkg}.db"
        try:
            subprocess.run(f"su -c 'cp {db_origem} {db_temp} && chmod 777 {db_temp}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except: continue

        if os.path.exists(db_temp):
            token_ativo = None
            try:
                conn = sqlite3.connect(db_temp)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cookies WHERE name='.ROBLOSECURITY' ORDER BY last_access_utc DESC LIMIT 1")
                row = cursor.fetchone()
                conn.close()

                if row and row[0] and "_|WARNING" in row[0] and len(row[0]) >= MIN_TOKEN_LENGTH:
                    token_ativo = row[0]
            except: pass
            finally:
                if os.path.exists(db_temp):
                    os.remove(db_temp)
            
            if token_ativo:
                return token_ativo
    return None

def monitor_loop():
    limpar_zumbis()
    verificar_ou_criar_tarefas_pendentes()
    print(f"\n[🔄 MONITOR] Vigia de tokens multiplataforma ativa (Ciclo: {LOOP_INTERVAL}s)...")
    sys.stdout.flush()

    while True:
        try:
            try:
                cmd = "su -c 'ls /data/data | grep -i roblox'"
                resultado = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5).decode('utf-8').strip()
                pacotes = [p for p in resultado.split('\n') if p]
            except: pacotes = []

            dados_salvos = load_saved_tokens()
            houve_mudanca = False

            # Limpa APKs que foram desinstalados
            pacotes_salvos = list(dados_salvos.keys())
            for pkg_salvo in pacotes_salvos:
                if pkg_salvo not in pacotes:
                    print(f"[🗑️] APK {pkg_salvo} desinstalado. Removendo do registro...")
                    del dados_salvos[pkg_salvo]
                    houve_mudanca = True

            for pkg in pacotes:
                token_ativo = extract_active_token(pkg)
                if not token_ativo: continue
                
                if pkg not in dados_salvos:
                    dados_salvos[pkg] = {}

                username = get_roblox_username(token_ativo)
                if not username:
                    username = f"Conta_Desconhecida_{pkg}"

                # Tira o Focus de TODAS as contas desse pacote e converte formato antigo pra novo
                for user, info in dados_salvos[pkg].items():
                    if isinstance(info, dict):
                        if info.get("Focus", False):
                            dados_salvos[pkg][user]["Focus"] = False
                            houve_mudanca = True
                    elif isinstance(info, str):
                        dados_salvos[pkg][user] = {"token": info, "Focus": False}
                        houve_mudanca = True

                # Define a conta extraída do Cookie como a conta FOCUS atual
                conta_anterior = dados_salvos[pkg].get(username, {})
                token_anterior = conta_anterior.get("token", "")

                if token_ativo != token_anterior:
                    print(f"\n⭐ [NOVO LOGIN / ATUALIZOU] Pacote: {pkg} | Conta Focus: {username}")
                    dados_salvos[pkg][username] = {"token": token_ativo, "Focus": True}
                    houve_mudanca = True
                else:
                    # Se o token for igual, mas ela não era o Focus, agora ela é
                    if not conta_anterior.get("Focus", False):
                        print(f"\n⭐ [MUDANÇA DE FOCO] A conta {username} agora é a principal em {pkg}")
                        dados_salvos[pkg][username]["Focus"] = True
                        houve_mudanca = True

            if houve_mudanca:
                save_to_json(dados_salvos)

        except KeyboardInterrupt:
            print("\n[🛑] Encerrando...")
            limpar_zumbis()
            sys.exit(0)
        except Exception as e:
            pass # Silencia erros no loop para não floodar a tela
            
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    monitor_loop()
