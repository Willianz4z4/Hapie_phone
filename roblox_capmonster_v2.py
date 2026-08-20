import os
import sys

# ==========================================
# 🧠 SISTEMA DE AUTO-INSTALAÇÃO (BOOTSTRAP)
# ==========================================
if "--ubuntu-run" not in sys.argv and "com.termux" in sys.executable:
    print("🚀 [SISTEMA] Rodando no Termux! Verificando ambiente e pulando pro Ubuntu...")
    os.system("command -v proot-distro > /dev/null 2>&1 || (pkg update -y && pkg install proot-distro -y)")
    os.system("proot-distro install ubuntu > /dev/null 2>&1")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    nome_script = os.path.basename(__file__)

    sh_temp = os.path.join(script_dir, ".run_ubuntu_temp.sh")
    comando_ubuntu = f"""#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
if ! command -v python3 > /dev/null 2>&1; then
    apt-get update -y && apt-get install python3 python3-pip -y;
fi
if ! python3 -c 'import patchright' > /dev/null 2>&1; then
    pip3 install patchright requests --break-system-packages && python3 -m patchright install chromium;
fi
cd /app
python3 {nome_script} --ubuntu-run
"""
    with open(sh_temp, "w") as f:
        f.write(comando_ubuntu)
    os.system(f"chmod +x {sh_temp}")
    os.system(f"proot-distro login ubuntu --bind '{script_dir}:/app' -- bash /app/.run_ubuntu_temp.sh")
    if os.path.exists(sh_temp):
        os.remove(sh_temp)
    sys.exit()

# ==========================================
# 🤖 IMPORTS DO BOT
# ==========================================
import time, json, requests, re
from urllib.parse import unquote, parse_qs
from patchright.sync_api import sync_playwright

# ==========================================
# ⚙️ CONFIGURAÇÕES
# ==========================================
USER = "Alaquelegalz4"
PASS = "willianz4z4oof$"
COOKIE_FILE = "cookies.json"
ERROR_LOG_FILE = "debug_erro_roblox.log"
CM_KEY = "35e32346fa20ab9dfa29b14e7809de2d"
ALVO_URL = "https://www.roblox.com/login"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

dados_capturados = {"blob": None, "pk": None, "surl": None, "challenge_id": None}

def salvar_log_erro(etapa, res, payload=None, headers=None):
    with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== ERRO NA ETAPA: {etapa} ===\n")
        f.write(f"Status Code: {res.status_code}\n")
        f.write(f"Headers da Resposta: {json.dumps(dict(res.headers), indent=4)}\n")
        f.write(f"Corpo da Resposta: {res.text}\n")
        if payload:
            f.write(f"\nPayload Enviado: {json.dumps(payload, indent=4)}\n")
        if headers:
            f.write(f"\nHeaders Enviados: {json.dumps(dict(headers), indent=4)}\n")
    print(f"\n[!] Log de erro detalhado salvo em: {ERROR_LOG_FILE}")

def interceptador_rede(route):
    if "fc/gt2/public_key/" in route.request.url and route.request.method == "POST":
        print(f"\n[🚨] Interceptando Arkose...")
        try:
            dados_capturados['pk'] = route.request.url.split('/')[-1]
            match_surl = re.search(r'https?://([^/]+)', route.request.url)
            if match_surl: dados_capturados['surl'] = match_surl.group(1)

            payload = parse_qs(route.request.post_data)
            for chave in payload:
                if 'blob' in chave.lower():
                    dados_capturados['blob'] = unquote(payload[chave][0])
                    print(f"[🔥] Blob Capturado! Tamanho: {len(dados_capturados['blob'])}")
        except Exception as e: 
            print(f"[!] Erro ao capturar blob: {e}")
        route.abort()
    else:
        route.continue_()

def captura_challenge(response):
    if "v2/login" in response.url and response.status == 403:
        chal_id = response.headers.get("rblx-challenge-id")
        if chal_id:
            dados_capturados['challenge_id'] = chal_id
            print(f"[🔥] Challenge ID capturado: {chal_id}")

def solve_captcha(blob, pk, surl):
    print(f"[*] Enviando para CapMonster...")
    task_data = {
        'type': 'FunCaptchaTaskProxyless', 
        'websiteURL': ALVO_URL, 
        'websitePublicKey': pk, 
        'data': json.dumps({'blob': blob})
    }
    if surl: 
        task_data['funcaptchaApiJSSubdomain'] = surl

    try:
        t_res = requests.post('https://api.capmonster.cloud/createTask', json={'clientKey': CM_KEY, 'task': task_data}).json()
        t_id = t_res.get('taskId')
        if not t_id: 
            print("[-] Falha ao criar tarefa no CapMonster.")
            return None

        for _ in range(40):
            time.sleep(3)
            res = requests.post('https://api.capmonster.cloud/getTaskResult', json={'clientKey': CM_KEY, 'taskId': t_id}).json()
            if res.get('status') == 'ready': 
                return res.get('solution', {}).get('token')
            elif res.get('status') == 'processing':
                continue
            else:
                print(f"[-] Erro no CapMonster: {res}")
                return None
    except Exception as e:
        print(f"[-] Erro de conexão com CapMonster: {e}")
    return None

# ==========================================
# 🚀 EXECUÇÃO PRINCIPAL
# ==========================================
def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage'])
        c = b.new_context(user_agent=USER_AGENT)
        page = c.new_page()
        page.route("**/*", interceptador_rede)
        page.on("response", captura_challenge)

        print(f"\n[+] Acessando Login...")
        try:
            page.goto(ALVO_URL, timeout=60000)
            page.fill('input#login-username', USER)
            page.fill('input#login-password', PASS)
            page.click('button#login-button')
        except Exception as e:
            print(f"[-] Erro ao carregar página: {e}")
            b.close()
            return

        print("[*] Aguardando Arkose...")
        for _ in range(30):
            time.sleep(1)
            if dados_capturados['blob'] and dados_capturados['challenge_id']: break

        if dados_capturados['blob'] and dados_capturados['challenge_id']:
            token = solve_captcha(dados_capturados['blob'], dados_capturados['pk'], dados_capturados['surl'])

            if token:
                print(f"[+] Token recebido. Iniciando API...")

                session = requests.Session()
                session.headers.update({"User-Agent": USER_AGENT, "Origin": "https://www.roblox.com", "Referer": ALVO_URL})

                for cookie in c.cookies():
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

                # 2. Pegar CSRF
                print(f"[*] Buscando CSRF Token...")
                csrf_res = session.post("https://auth.roblox.com/v2/login")
                csrf = csrf_res.headers.get("x-csrf-token", "")
                if not csrf:
                    print("[-] ALERTA: CSRF Token não encontrado no cabeçalho!")
                session.headers.update({"X-CSRF-TOKEN": csrf})

                # 3. Postar Challenge (V1 Continue)
                print(f"[*] Postando Challenge...")
                chal_payload = {
                    "challengeId": dados_capturados['challenge_id'],
                    "challengeType": "captcha",
                    "metadata": json.dumps({"verificationToken": token})
                }
                res_chal = session.post("https://apis.roblox.com/challenge/v1/continue", json=chal_payload)
                print(f"[DEBUG] Challenge Res ({res_chal.status_code}): {res_chal.text}")
                
                if res_chal.status_code not in [200, 204]:
                    salvar_log_erro("V1_CONTINUE", res_chal, chal_payload, session.headers)

                # 4. Postar Login V2
                print(f"[*] Postando Login Final...")
                login_payload = {
                    "ctype": "Username", "cvalue": USER, "password": PASS,
                    "captchaToken": token, "captchaId": dados_capturados['challenge_id'], "captchaProvider": "PROVIDER_ARKOSE_LABS"
                }
                
                res_login = session.post("https://auth.roblox.com/v2/login", json=login_payload)
                print(f"[DEBUG] Login Res ({res_login.status_code}): {res_login.text}")

                if res_login.status_code == 200 and ".ROBLOSECURITY" in session.cookies:
                    print("\n[+] VITÓRIA! Cookie capturado!")
                    with open(COOKIE_FILE, 'w') as f: 
                        json.dump(session.cookies.get_dict(), f, indent=4)
                else:
                    print(f"\n[-] Login falhou com status {res_login.status_code}.")
                    salvar_log_erro("V2_LOGIN_FINAL", res_login, login_payload, session.headers)
        else:
            print("[-] Falha: Não foi possível capturar os dados do Arkose ou o Challenge ID.")

        c.close()
        b.close()

if __name__ == "__main__":
    main()
