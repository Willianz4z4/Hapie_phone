import os
import sys
import time
import json
import random
import requests
from datetime import datetime

PROJECT_ROOT = "/app" if os.path.exists("/app/Data") else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
AVATAR_DIR = os.path.join(PROJECT_ROOT, "Data", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def upload_to_nuvem(file_path):
    print("[☁️] Fazendo upload da foto de perfil para a nuvem...")
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://freeimage.host/api/1/upload",
                data={"key": "6d207e02198a847aa98d0a2a901485a5", "action": "upload", "format": "json"},
                files={"source": f},
                timeout=20
            )
        if res.status_code == 200:
            data = res.json()
            if "image" in data and "url" in data["image"]:
                url = data["image"]["url"]
                print(f"✅ [NUVEM] Upload concluído! URL: {url}")
                return url
    except Exception as e:
        print(f"[!] Erro no upload: {e}")
    return None

def update_external_setup(pkg, username, roblox_data):
    """Atualiza os dados de uma conta específica dentro do pacote pai no apps_install.json"""
    caminhos = [
        os.path.join(PROJECT_ROOT, "Data", "apps_install.json"),
        "/sdcard/apps_install.json"
    ]
    json_path = next((c for c in caminhos if os.path.exists(c)), None)  
    if not json_path:
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            apps_db = json.load(f)

        if pkg in apps_db:
            ext_setup = apps_db[pkg].get("external_setup", {})
            if not isinstance(ext_setup, dict):
                ext_setup = {}
            
            # Cria a estrutura de múltiplas contas por pacote
            if "roblox_accounts" not in ext_setup or not isinstance(ext_setup["roblox_accounts"], dict):
                ext_setup["roblox_accounts"] = {}                       
            if username not in ext_setup["roblox_accounts"]:
                ext_setup["roblox_accounts"][username] = {}             
            ext_setup["roblox_accounts"][username].update(roblox_data)
            apps_db[pkg]["external_setup"] = ext_setup                  
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(apps_db, f, indent=4, ensure_ascii=False)     
            print(f"💾 [INTEGRAÇÃO] Dados da conta '{username}' salvos no external_setup do pacote {pkg}!")
    except Exception as e:
        print(f"[!] Erro ao injetar dados no apps_install.json: {e}")

def change_display_name(pkg=None, token=None, novo_nome=None):
    if not token or not novo_nome:
        print("[!] Token ou Novo Nome ausentes para alteração de Display Name.")
        return False

    token = token.strip().replace('"', '').replace("'", "")
    novo_nome = str(novo_nome).strip()
    print(f"\n[✏️ DISPLAY NAME] Tentando alterar para: '{novo_nome}'...")

    session = requests.Session()
    session.cookies[".ROBLOSECURITY"] = token
    session.headers.update({"User-Agent": USER_AGENT})
    auth_req = session.get("https://users.roblox.com/v1/users/authenticated")                                                                   
    if auth_req.status_code != 200:
        print("[!] Token inválido ou expirado. Não foi possível autenticar.")
        return False                                                    
    user_data = auth_req.json()
    user_id = user_data.get("id")
    username = user_data.get("name")
    nome_atual = user_data.get("displayName")
    print(f"[*] Conta: {username} | Display Name atual: {nome_atual}")

    url_patch = f"https://users.roblox.com/v1/users/{user_id}/display-names"
    payload = {"newDisplayName": novo_nome}                             
    req = session.patch(url_patch, json=payload)
    if req.status_code == 403 and "x-csrf-token" in req.headers:
        session.headers["x-csrf-token"] = req.headers["x-csrf-token"]
        req = session.patch(url_patch, json=payload)                    
    if req.status_code == 200:
        print(f"[✅] Sucesso! Display Name alterado para: {novo_nome}")
        if pkg:
            update_external_setup(pkg, username, {"display_name": novo_nome})
        return True
    else:
        try:
            msg_erro = req.json().get("errors", [{}])[0].get("message", req.text)
        except Exception:
            msg_erro = req.text
        print(f"[❌] Falha ao alterar Display Name. Motivo: {msg_erro}")
        return False                                                    

def extract_account_value(token):
    print("[🔍] Extraindo saldo de Robux e RAP...")
    session = requests.Session()
    session.cookies[".ROBLOSECURITY"] = token
    
    auth_req = session.get("https://users.roblox.com/v1/users/authenticated")
    if auth_req.status_code != 200: return {}
    user_id = auth_req.json().get("id")
    user_info_req = session.get(f"https://users.roblox.com/v1/users/{user_id}")
    created_str = user_info_req.json().get("created", "") if user_info_req.status_code == 200 else ""
    bonus_idade = 0
    data_criacao_formatada = "Unknown"
    
    if created_str:
        try:
            data_criacao = datetime.strptime(created_str[:10], "%Y-%m-%d")
            data_criacao_formatada = data_criacao.strftime("%d/%m/%Y")
            anos_conta = (datetime.now() - data_criacao).days / 365.25
            if anos_conta > 0: bonus_idade = int(500 * (1.35 ** anos_conta))
        except: pass                                                    
    robux_req = session.get(f"https://economy.roblox.com/v1/users/{user_id}/currency")                                                              robux_balance = robux_req.json().get("robux", 0) if robux_req.status_code == 200 else 0

    total_rap = 0
    cursor = ""
    while True:
        url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?sortOrder=Asc&limit=100"
        if cursor: url += f"&cursor={cursor}"
        rap_req = session.get(url)
        if rap_req.status_code == 200:
            data = rap_req.json()
            total_rap += sum([i.get("recentAveragePrice", 0) for i in data.get("data", []) if i.get("recentAveragePrice")])
            cursor = data.get("nextPageCursor")
            if not cursor: break
            time.sleep(0.1)
        else: break
    potential_value = robux_balance + total_rap + bonus_idade

    return {
        "robux_balance": robux_balance,
        "creation_date": data_criacao_formatada,
        "potential_value": potential_value
    }

def update_servelink(pkg, username, token):
    print(f"\n[🔗] Verificando e atualizando dados completos dos VIPs para '{username}' ({pkg})")
    session = requests.Session()
    session.cookies[".ROBLOSECURITY"] = token
    session.headers.update({"Content-Type": "application/json"})
    
    def safe_request(method, url, **kwargs):
        for _ in range(3):
            try:
                res = session.request(method, url, **kwargs)
                if res.status_code == 403 and "x-csrf-token" in res.headers:
                    session.headers["x-csrf-token"] = res.headers["x-csrf-token"]
                    res = session.request(method, url, **kwargs)
                if res.status_code == 429:
                    time.sleep(1)
                    continue
                return res
            except Exception:
                time.sleep(1)
        return None                                                     
    
    vips_encontrados = []
    cursor = ""
    while True:
        url = "https://games.roblox.com/v1/private-servers/my-private-servers?itemsPerPage=100&privateServersTab=MyPrivateServers"
        if cursor: url += f"&cursor={cursor}"
        res = safe_request("GET", url)
        if res and res.status_code == 200:
            data = res.json()
            vips_encontrados.extend(data.get("data", []))
            cursor = data.get("nextPageCursor")
            if not cursor: break
            time.sleep(0.5)
        else: break

    private_servers_array = []
    for vip in vips_encontrados:
        vip_id = str(vip.get("vipServerId") or vip.get("privateServerId") or vip.get("id") or "")
        fallback_nome = vip.get("name", "Desconhecido")
        if not vip_id: continue                                         
        req_det = safe_request("GET", f"https://games.roblox.com/v1/vip-servers/{vip_id}")
        if req_det and req_det.status_code == 200:
            det = req_det.json()
            is_active_geral = det.get("active", False)
            subscription = det.get("subscription", {})
            is_expired = subscription.get("expired", False)
            jogo_nome = det.get("game", {}).get("name", fallback_nome)
            deletado = "[ Content Deleted ]" in jogo_nome

            game_id = det.get("game", {}).get("id")
            is_playable = False

            if game_id and not deletado and not is_expired:
                req_status = safe_request("GET", f"https://games.roblox.com/v1/games/multiget-playability-status?universeIds={game_id}")
                if req_status and req_status.status_code == 200:
                    status_data = req_status.json()
                    if status_data and isinstance(status_data, list):
                        is_playable = status_data[0].get("isPlayable", False)

            if not is_playable or is_expired:
                if is_active_geral:
                    safe_request("PATCH", f"https://games.roblox.com/v1/vip-servers/{vip_id}", json={"active": False})
                continue                                                
            private_servers_array.append({
                "identificacao": {"vip_id": vip_id, "nome_servidor": det.get("name", fallback_nome)},
                "status_e_financas": {"ativo": True},
                "dados_completos": det
            })
        time.sleep(0.1)

    if private_servers_array:
        update_external_setup(pkg, username, {"private_servers": private_servers_array})

def picture_profile(pkg=None, token=None, is_focused=False):
    if not token: return False
    token = token.strip().replace('"', '').replace("'", "")
    print(f"\n[🖼️ PROFILE] Extraindo dados da conta e avatar ({pkg or 'manual'})...")
    
    # Agora o script embute se a conta está ativa (Focus) no momento
    dados_conta = {"username": "Desconhecido", "display_name": "Desconhecido", "user_id": 0, "avatar_url": None, "Focus": is_focused}
    
    try:
        s = requests.Session()
        s.cookies.set(".ROBLOSECURITY", token, domain=".roblox.com")
        res_api = s.get("https://users.roblox.com/v1/users/authenticated", headers={"User-Agent": USER_AGENT}, timeout=10)
        if res_api.status_code == 200:
            user_info = res_api.json()
            dados_conta["username"] = user_info.get('name')
            dados_conta["display_name"] = user_info.get('displayName')
            dados_conta["user_id"] = user_info.get('id')
            print(f"[+] Usuário identificado: {dados_conta['username']} (ID: {dados_conta['user_id']})")
    except Exception as e: print(f"[!] Erro API: {e}")                  
    username = dados_conta["username"]

    if dados_conta["user_id"]:
        try:
            print("[*] Baixando avatar oficial via API Roblox...")
            thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={dados_conta['user_id']}&size=420x420&format=Png&isCircular=false"
            res_thumb = requests.get(thumb_url, timeout=10)
            if res_thumb.status_code == 200:
                img_url = res_thumb.json().get("data", [{}])[0].get("imageUrl")
                if img_url:
                    file_path = os.path.join(AVATAR_DIR, f"{(pkg or 'roblox').replace('.', '_')}_{username}_{int(time.time())}.png")
                    res_img = requests.get(img_url, timeout=15)
                    if res_img.status_code == 200:
                        with open(file_path, "wb") as f: f.write(res_img.content)
                        nuvem_url = upload_to_nuvem(file_path)
                        if nuvem_url: dados_conta["avatar_url"] = nuvem_url
        except Exception as e: print(f"[!] Erro Avatar: {e}")
        
        dados_conta.update(extract_account_value(token))
        
    update_external_setup(pkg, username, dados_conta)
    update_servelink(pkg, username, token)
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--rename" and len(sys.argv) > 2:
            novo_nome = sys.argv[2]
            caminhos = ["/app/Data/Roblox_token.json", "/sdcard/Roblox_token.json"]
            data_file = next((c for c in caminhos if os.path.exists(c)), None)
            if data_file:
                with open(data_file, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                    if tokens:
                        pkg_sorteado = random.choice(list(tokens.keys()))
                        contas_dict = tokens[pkg_sorteado]
                        if isinstance(contas_dict, dict) and contas_dict:
                            user_sorteado = random.choice(list(contas_dict.keys()))
                            info_conta = contas_dict[user_sorteado]
                            
                            # Adaptação para o novo formato de JSON
                            token_str = info_conta.get("token") if isinstance(info_conta, dict) else info_conta
                            
                            change_display_name(pkg=pkg_sorteado, token=token_str, novo_nome=novo_nome)
    else:
        caminhos = ["/app/Data/Roblox_token.json", "/sdcard/Roblox_token.json"]
        data_file = next((c for c in caminhos if os.path.exists(c)), None)
        if data_file:
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                if tokens:
                    pkg_sorteado = random.choice(list(tokens.keys()))
                    contas_dict = tokens[pkg_sorteado]
                    if isinstance(contas_dict, dict) and contas_dict:
                        user_sorteado = random.choice(list(contas_dict.keys()))
                        info_conta = contas_dict[user_sorteado]
                        
                        # Adaptação para o novo formato de JSON (extrai o token e o Focus)
                        token_str = info_conta.get("token") if isinstance(info_conta, dict) else info_conta
                        is_focused = info_conta.get("Focus", False) if isinstance(info_conta, dict) else False
                        
                        picture_profile(pkg=pkg_sorteado, token=token_str, is_focused=is_focused)
            except: pass
