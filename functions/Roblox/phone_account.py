import os
import sys
import json
import time
import sqlite3
import subprocess
from datetime import datetime

LOOP_INTERVAL = 10
MIN_TOKEN_LENGTH = 500  # Token válido tem +700 caracteres

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

def get_data_dir():
    data_dir = os.path.join(PROJECT_ROOT, "Data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def load_saved_tokens():
    json_path = os.path.join(get_data_dir(), "Roblox_token.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_to_json(dados_salvos):
    json_path = os.path.join(get_data_dir(), "Roblox_token.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados_salvos, f, indent=4, ensure_ascii=False)
    print(f"💾 [SALVO] Token atualizado com sucesso em: {json_path}")

def chamar_picture_profile_bg(pkg, token):
    print(f"🚀 [ASSISTANCE] Disparando tarefa em 2º plano para {pkg}...")
    cmd = [
        "proot-distro", "login", "ubuntu",
        "--bind", f"{PROJECT_ROOT}:/app",
        "--bind", "/sdcard:/sdcard",
        "--", "bash", "-c",
        f"cd /app/functions/Roblox/Roblox_google && python3 -c \"import phone_assistance; phone_assistance.picture_profile(pkg='{pkg}', token='''{token}''')\""
    ]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[!] Erro ao iniciar processo em 2º plano: {e}")

def extract_single_package(pkg):
    """Copia o banco de dados do Roblox e lê via Python para não cortar o texto"""
    locais_db = [
        f"/data/data/{pkg}/app_webview/Default/Cookies",
        f"/data/data/{pkg}/app_webview/Default/Network/Cookies"
    ]
    
    for db_origem in locais_db:
        db_temp = f"/data/data/com.termux/files/home/temp_cookie_{pkg}.db"
        
        # Copia o arquivo protegido para o Termux e dá permissão
        os.system(f"su -c 'cp {db_origem} {db_temp} && chmod 777 {db_temp}' 2>/dev/null")
        
        if os.path.exists(db_temp):
            try:
                conn = sqlite3.connect(db_temp)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cookies WHERE name='.ROBLOSECURITY'")
                row = cursor.fetchone()
                conn.close()
                
                if row and row[0]:
                    token = row[0]
                    # Verifica se extraiu inteiro
                    if "_|WARNING" in token and len(token) >= MIN_TOKEN_LENGTH:
                        os.remove(db_temp)
                        return token
            except Exception:
                pass
            finally:
                if os.path.exists(db_temp):
                    os.remove(db_temp)
                    
    return None

def monitor_loop():
    print(f"\n[🔄 MONITOR] Vigia de tokens do Roblox ativa (Ciclo: {LOOP_INTERVAL}s)...")

    while True:
        try:
            cmd_packages = "su -c 'ls /data/data | grep -i roblox'"
            try:
                resultado = subprocess.check_output(cmd_packages, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                pacotes = [p for p in resultado.split('\n') if p]
            except Exception:
                time.sleep(LOOP_INTERVAL)
                continue

            if not pacotes:
                time.sleep(LOOP_INTERVAL)
                continue

            dados_salvos = load_saved_tokens()
            houve_mudanca = False

            for pkg in pacotes:
                token_completo = extract_single_package(pkg)
                if not token_completo:
                    continue

                registro_anterior = dados_salvos.get(pkg, {})
                token_anterior = registro_anterior.get("token", "")

                if token_completo != token_anterior:
                    print(f"\n⚡ [ATUALIZAÇÃO DE TOKEN] Pacote: {pkg}")
                    print(f"   📏 Tamanho capturado: {len(token_completo)} caracteres")

                    dados_salvos[pkg] = {
                        "package": pkg,
                        "token": token_completo,
                        "updated_at": datetime.now().isoformat()
                    }
                    houve_mudanca = True
                    
                    chamar_picture_profile_bg(pkg, token_completo)

            if houve_mudanca:
                save_to_json(dados_salvos)

        except KeyboardInterrupt:
            print("\n[🛑] Monitoramento finalizado.")
            break
        except Exception as e:
            print(f"[!] Erro no loop principal: {e}")

        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    monitor_loop()
