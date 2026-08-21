import os
import sys
import time
import json
import random
import requests
from datetime import datetime
from patchright.sync_api import sync_playwright

PROJECT_ROOT = "/app" if os.path.exists("/app/Data") else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
AVATAR_DIR = os.path.join(PROJECT_ROOT, "Data", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)
#oi

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

ASSET_TYPES = {
    2: "T-Shirts", 11: "Shirts", 12: "Pants",
    8: "Hats", 18: "Faces", 19: "Gears", 34: "Game Passes",
    41: "Hair", 42: "Face Accessories", 43: "Neck Accessories", 44: "Shoulder Accessories",
    45: "Front Accessories", 46: "Back Accessories", 47: "Waist Accessories", 61: "Animations"
}

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

def update_external_setup(pkg, roblox_data):
    """Injeta os dados no apps_install.json mesclando com o que já existe (Não apaga a foto)"""
    caminhos = [
        os.path.join(PROJECT_ROOT, "Data", "apps_install.json"),
        "/sdcard/apps_install.json"
    ]
    json_path = next((c for c in caminhos if os.path.exists(c)), None)

    if not json_path:
        print("[!] Arquivo apps_install.json não encontrado. Registro pulado.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            apps_db = json.load(f)

        if pkg in apps_db:
            ext_setup = apps_db[pkg].get("external_setup", {})
            if not isinstance(ext_setup, dict):
                ext_setup = {}

            if "roblox_account" not in ext_setup:
                ext_setup["roblox_account"] = {}

            # Atualiza apenas as chaves novas, mantendo as antigas
            ext_setup["roblox_account"].update(roblox_data)
            apps_db[pkg]["external_setup"] = ext_setup

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(apps_db, f, indent=4, ensure_ascii=False)

            print(f"💾 [INTEGRAÇÃO] Dados salvos no external_setup do {pkg}!")
        else:
            print(f"[!] O pacote {pkg} não está listado no apps_install.json.")

    except Exception as e:
        print(f"[!] Erro ao injetar dados no apps_install.json: {e}")

def extract_account_value(token):
    """Motor de extração profunda que devolve os dados de valor da conta"""
    print("[🔍] Extraindo dados financeiros e de inventário...")
    session = requests.Session()
    session.cookies[".ROBLOSECURITY"] = token

    def post_com_csrf(url, payload):
        req = session.post(url, json=payload)
        if req.status_code == 403 and "x-csrf-token" in req.headers:
            session.headers["x-csrf-token"] = req.headers["x-csrf-token"]
            req = session.post(url, json=payload)
        return req

    auth_req = session.get("https://users.roblox.com/v1/users/authenticated")
    if auth_req.status_code != 200:
        return {}

    user_id = auth_req.json().get("id")

    # 1. Idade da conta
    user_info_req = session.get(f"https://users.roblox.com/v1/users/{user_id}")
    created_str = user_info_req.json().get("created", "") if user_info_req.status_code == 200 else ""
    bonus_idade = 0
    data_criacao_formatada = "Unknown"
    if created_str:
        try:
            data_criacao = datetime.strptime(created_str[:10], "%Y-%m-%d")
            data_criacao_formatada = data_criacao.strftime("%d/%m/%Y")
            anos_conta = (datetime.now() - data_criacao).days / 365.25
            if anos_conta > 0:
                bonus_idade = int(500 * (1.35 ** anos_conta))
        except: pass

    # 2. Robux
    robux_req = session.get(f"https://economy.roblox.com/v1/users/{user_id}/currency")
    robux_balance = robux_req.json().get("robux", 0) if robux_req.status_code == 200 else 0

    # 3. Limiteds RAP
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
        elif rap_req.status_code == 429:
            time.sleep(3)
        else: break

    # 4. Escaneamento Profundo
    all_assets = []
    for asset_type, type_name in ASSET_TYPES.items():
        cursor = ""
        while True:
            url = f"https://inventory.roblox.com/v2/users/{user_id}/inventory/{asset_type}?limit=100&sortOrder=Desc"
            if cursor: url += f"&cursor={cursor}"
            req = session.get(url)
            if req.status_code == 200:
                data = req.json()
                for item in data.get("data", []):
                    aid = item.get("assetId")
                    nome = item.get("assetName") or item.get("name") or f"Item {aid}"
                    if aid:
                        all_assets.append({"id": aid, "name": nome, "type": asset_type, "type_name": type_name})
                cursor = data.get("nextPageCursor")
                if not cursor: break
                time.sleep(0.05)
            elif req.status_code == 429:
                time.sleep(3)
            else: break

    robux_gasto_itens = 0
    estimativa_offsale = 0
    robux_spent = []

    for i in range(0, len(all_assets), 120):
        chunk = all_assets[i:i+120]
        batch = [{"itemType": "Asset", "id": item["id"]} for item in chunk]
        res = post_com_csrf("https://catalog.roblox.com/v1/catalog/items/details", {"items": batch})

        catalog_info = {}
        if res.status_code == 200:
            for c_item in res.json().get("data", []):
                if c_item.get("id"):
                    catalog_info[str(c_item["id"])] = c_item

        for item in chunk:
            aid = str(item["id"])
            c_item = catalog_info.get(aid, {})
            preco = c_item.get("price")

            if preco is not None and preco > 0:
                robux_gasto_itens += preco
                robux_spent.append({"name": item["name"], "price": preco, "type": item["type_name"]})
            else:
                tid = item["type"]
                if tid in [8, 18, 19, 41, 42, 43, 44, 45, 46, 47, 61]: estimativa_offsale += 50
                elif tid in [2, 11, 12]: estimativa_offsale += 5
                elif tid == 34: estimativa_offsale += 100
        time.sleep(0.15)

    robux_spent.sort(key=lambda x: x["price"], reverse=True)
    potential_value = robux_balance + total_rap + robux_gasto_itens + estimativa_offsale + bonus_idade

    return {
        "robux_balance": robux_balance,
        "creation_date": data_criacao_formatada,
        "potential_value": potential_value,
        "robux_spent": robux_spent
    }

def update_servelink(pkg, token):
    """Verifica e atualiza os Servidores VIP de forma completa, salvando no array private_servers"""
    print(f"\n[🔗] Verificando e atualizando dados completos dos VIPs: {pkg}")
    session = requests.Session()
    session.cookies[".ROBLOSECURITY"] = token
    session.headers.update({"Content-Type": "application/json"})

    def safe_request(method, url, **kwargs):
        max_retries = 3
        delay = 1.0
        for attempt in range(max_retries):
            try:
                res = session.request(method, url, **kwargs)
                if res.status_code == 403 and "x-csrf-token" in res.headers:
                    session.headers["x-csrf-token"] = res.headers["x-csrf-token"]
                    res = session.request(method, url, **kwargs)
                if res.status_code == 429:
                    time.sleep(delay)
                    delay *= 2
                    continue
                return res
            except:
                time.sleep(delay)
                delay *= 2
        return None

    auth_check = safe_request("POST", "https://auth.roblox.com/v2/login")
    req = safe_request("GET", "https://users.roblox.com/v1/users/authenticated")

    if not req or req.status_code != 200:
        print("[!] Token inválido, ignorando VIPs.")
        return

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
        vip_id = str(vip.get("id") or vip.get("vipServerId", ""))
        if not vip_id: continue

        req_det = safe_request("GET", f"https://games.roblox.com/v1/vip-servers/{vip_id}")
        if req_det and req_det.status_code == 200:
            det = req_det.json()
            is_active = det.get("active", False)
            jogo_nome = det.get("game", {}).get("name", "Desconhecido")
            deletado = "[ Content Deleted ]" in jogo_nome

            # Ignora servidores desativados ou deletados
            if not is_active or deletado:
                continue

            # Tenta gerar link novo se não houver nenhum
            if not det.get("link") and not det.get("joinCode"):
                patch_req = safe_request("PATCH", f"https://games.roblox.com/v1/vip-servers/{vip_id}", json={"newJoinCode": True})
                if patch_req and patch_req.status_code == 200:
                    novo_det = patch_req.json()
                    if novo_det.get("link") or novo_det.get("joinCode"):
                        det = novo_det

            place_id = det.get("game", {}).get("rootPlace", {}).get("id", "")
            join_code = det.get("joinCode")

            link_direto = det.get("link")
            if not link_direto and join_code and place_id:
                link_direto = f"https://www.roblox.com/games/{place_id}?privateServerLinkCode={join_code}"

            if link_direto:
                # Injetamos a estrutura rica no array
                private_servers_array.append({
                    "identificacao": {
                        "vip_id": vip_id,
                        "nome_servidor": det.get("name", "Desconhecido"),
                    },
                    "jogo": {
                        "place_id": place_id,
                        "nome_jogo": jogo_nome,
                        "deletado_pelo_roblox": deletado,
                        "desativado_pelo_criador": False
                    },
                    "status_e_financas": {
                        "ativo": is_active,
                        "preco_robux": det.get("subscription", {}).get("price", 0),
                        "data_expiracao": det.get("subscription", {}).get("expirationDate"),
                        "sem_saldo_para_renovar": det.get("subscription", {}).get("hasInsufficientFunds", False)
                    },
                    "link_entrar_direto": link_direto,
                    "permissoes": {
                        "amigos_permitidos": det.get("permissions", {}).get("friendsAllowed", False),
                        "membros_whitelist_ids": [str(u.get("id")) for u in det.get("permissions", {}).get("users", [])]
                    },
                    "extras": {
                        "chat_de_voz_ativo": det.get("voiceSettings", {}).get("enabled", False)
                    }
                })
        time.sleep(0.5)

    if private_servers_array:
        print(f"[✅] {len(private_servers_array)} servidores VIP salvos com dados completos.")
        update_external_setup(pkg, {"private_servers": private_servers_array})
    else:
        print(f"[⚪] Nenhum servidor VIP ativo encontrado para o pacote {pkg}.")

def picture_profile(pkg=None, token=None):
    if not token:
        print("[!] Token ROBLOSECURITY não informado.")
        return False

    token = token.strip().replace('"', '').replace("'", "")
    print(f"\n[🖼️ PROFILE] Extraindo dados da conta e avatar ({pkg or 'manual'})...")

    dados_conta = {
        "username": "Desconhecido",
        "display_name": "Desconhecido",
        "user_id": 0,
        "avatar_url": None
    }

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
    except Exception as e:
        print(f"[!] Erro ao puxar dados da API: {e}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(user_agent=USER_AGENT)
            context.add_cookies([
                {"name": ".ROBLOSECURITY", "value": token, "domain": ".roblox.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"},
                {"name": ".ROBLOSECURITY", "value": token, "domain": "www.roblox.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"}
            ])

            page = context.new_page()
            print("[*] Carregando Roblox para capturar avatar...")
            page.goto("https://www.roblox.com/home", timeout=30000, wait_until="networkidle")
            time.sleep(3)

            safe_pkg = pkg.replace(".", "_") if pkg else "roblox"
            timestamp = int(time.time())

            img_selector = "span.avatar-card-image img, span.user-avatar-container img, a#nav-profile img, .navigation-user-avatar img"
            img_url = None

            try:
                page.wait_for_selector(img_selector, timeout=8000)
                img_url = page.locator(img_selector).first.get_attribute("src")
            except Exception:
                for img in page.locator("img").all():
                    src = img.get_attribute("src") or ""
                    if "thumbnails.roblox.com" in src or "avatar-headshot" in src:
                        img_url = src
                        break

            file_path = ""
            if img_url and img_url.startswith("http"):
                file_path = os.path.join(AVATAR_DIR, f"{safe_pkg}_{timestamp}.png")
                res = requests.get(img_url, timeout=15)
                if res.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(res.content)
            else:
                file_path = os.path.join(AVATAR_DIR, f"screenshot_{safe_pkg}_{timestamp}.png")
                page.screenshot(path=file_path)

            browser.close()

            if file_path and os.path.exists(file_path):
                nuvem_url = upload_to_nuvem(file_path)
                if nuvem_url:
                    dados_conta["avatar_url"] = nuvem_url
    except Exception as e:
        print(f"[!] Erro na captura visual: {e}")

    # Faz a varredura financeira e acopla nos dados antes de salvar
    dados_financeiros = extract_account_value(token)
    dados_conta.update(dados_financeiros)
    update_external_setup(pkg, dados_conta)

    # Chama a função de atualização de links VIP logo após puxar o perfil
    update_servelink(pkg, token)

    return True

def value_monitor_loop():
    """Roda a cada 24 horas atualizando o valor e links VIP de todas as contas"""
    print("\n[🔄] Iniciando Serviço de Auditoria de Contas (Loop 24h)...")
    caminhos = ["/app/Data/Roblox_token.json", "/sdcard/Roblox_token.json"]

    while True:
        data_file = next((c for c in caminhos if os.path.exists(c)), None)
        if data_file:
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                for pkg, d in tokens.items():
                    tk = d.get("token", "")
                    if tk:
                        print(f"\n[⏳] Atualizando valores e VIPs da conta no pacote: {pkg}")
                        dados_fin = extract_account_value(tk)
                        if dados_fin:
                            update_external_setup(pkg, dados_fin)
                        # Atualiza os links e permissões, salvando na chave private_servers
                        update_servelink(pkg, tk)
                        time.sleep(5)
            except Exception as e:
                print(f"[!] Erro no loop de monitoramento: {e}")

        print("[💤] Auditoria concluída. Hibernando por 24 horas...")
        time.sleep(86400) # Dorme 24 horas

def email(pkg=None, token=None, **kwargs): pass
def password(pkg=None, token=None, **kwargs): pass
def display_name(pkg=None, token=None, **kwargs): pass
def private_server(pkg=None, token=None, **kwargs): pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        value_monitor_loop()
    else:
        # Modo Teste Rápido
        caminhos = ["/app/Data/Roblox_token.json", "/sdcard/Roblox_token.json"]
        data_file = next((c for c in caminhos if os.path.exists(c)), None)
        if data_file:
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                if tokens:
                    pkg_sorteado = random.choice(list(tokens.keys()))
                    tk = tokens[pkg_sorteado].get("token", "")
                    picture_profile(pkg=pkg_sorteado, token=tk)
            except Exception as e:
                print(f"[!] Erro ao ler dados: {e}")
