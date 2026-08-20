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
# 🤖 IMPORTS DO BOT (SÓ RODAM DENTRO DO UBUNTU)
# ==========================================
import time, json, requests, re, base64
from urllib.parse import unquote
from patchright.sync_api import sync_playwright

USER = "Alaquelegalz4"
PASS = "willianz4z4oof$"
COOKIE_FILE = "cookies.json"
CM_KEY = "35e32346fa20ab9dfa29b14e7809de2d"
ALVO_URL = "https://www.roblox.com/login"

USAR_PROXY = True 

PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = 823
PROXY_USER = "66f8168c3d63dc0d5abd"
PROXY_PASS = "22a2f596131de837"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

dados_capturados = {
    "blob": None,
    "pk": None,
    "surl": None,
    "challenge_id": None
}

def interceptador_rede(route):
    request = route.request
    if "fc/gt2/public_key/" in request.url and request.method == "POST":
        print(f"\n[🚨 ALARME DE REDE] Requisição Arkose interceptada!")
        try:
            partes_url = request.url.split('/')
            dados_capturados['pk'] = partes_url[-1]
            match_surl = re.search(r'https?://([^/]+)', request.url)
            if match_surl:
                dados_capturados['surl'] = match_surl.group(1)

            payload_bruto = request.post_data
            if payload_bruto:
                match_blob = re.search(r'(?:data(?:%5B|\[)blob(?:%5D|\])|blob)=([^&]+)', payload_bruto)
                if match_blob:
                    blob_limpo = unquote(match_blob.group(1)).replace(' ', '+')
                    dados_capturados['blob'] = blob_limpo
                    print(f"[🔥 BINGO] Blob extraído! Tamanho: {len(blob_limpo)}")
        except Exception as e:
            print(f"[-] Erro no interceptador: {e}")
        route.abort()
    else:
        route.continue_()

def captura_challenge(response):
    if "v2/login" in response.url and response.status == 403:
        chal_id = response.headers.get("rblx-challenge-id")
        if chal_id:
            dados_capturados['challenge_id'] = chal_id
            print(f"\n[🔥] Challenge ID capturado: {chal_id}")

def solve(blob, pk, surl):
    print(f"[*] Montando Payload pro CapMonster...")
    task_data = {
        'type': 'FunCaptchaTaskProxyless' if not USAR_PROXY else 'FunCaptchaTask',
        'websiteURL': ALVO_URL,
        'websitePublicKey': pk,
        'userAgent': USER_AGENT
    }

    if USAR_PROXY:
        task_data.update({
            'proxyType': 'http', 'proxyAddress': PROXY_HOST,
            'proxyPort': PROXY_PORT, 'proxyLogin': PROXY_USER, 'proxyPassword': PROXY_PASS,
        })

    if surl: task_data['funcaptchaApiJSSubdomain'] = surl
    if blob: task_data['data'] = json.dumps({'blob': blob})

    try:
        t_res = requests.post('https://api.capmonster.cloud/createTask', json={'clientKey': CM_KEY, 'task': task_data}, timeout=20).json()
    except Exception:
        return None

    t = t_res.get('taskId')
    if not t: return None
    print(f"[*] Task ID: {t}. Aguardando resolução...")

    tentativas = 1
    while tentativas <= 80:
        time.sleep(3)
        try:
            res = requests.post('https://api.capmonster.cloud/getTaskResult', json={'clientKey': CM_KEY, 'taskId': t}, timeout=20).json()
        except: continue

        if res.get('errorId', 0) > 0: return None
        status = res.get('status')
        print(f"[*] [Tempo: {tentativas * 3}s] Status: {status}")

        if status == 'ready':
            print("\n✅ [+] CAPTCHA RESOLVIDO!")
            return res.get('solution', {}).get('token')
        tentativas += 1
    return None

with sync_playwright() as p:
    args_stealth = ['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,720', '--disable-web-security']
    print("\n[+] Iniciando Navegador...")
    
    b = p.chromium.launch(headless=True, args=args_stealth, proxy={'server': f'http://{PROXY_HOST}:{PROXY_PORT}', 'username': PROXY_USER, 'password': PROXY_PASS})
    c = b.new_context(user_agent=USER_AGENT, viewport={'width': 1280, 'height': 720})
    page = c.new_page()
    
    page.route("**/*", interceptador_rede)
    page.on("response", captura_challenge)

    MAX_RETRIES = 5
    for tentativa_atual in range(1, MAX_RETRIES + 1):
        dados_capturados['blob'] = None
        dados_capturados['pk'] = None
        dados_capturados['challenge_id'] = None

        print(f"\n==============================================")
        print(f"🚀 [RODADA {tentativa_atual}/{MAX_RETRIES}] Tentando autenticação...")
        print(f"==============================================")

        try:
            page.goto(ALVO_URL, wait_until="domcontentloaded", timeout=60000)
            page.fill('input#login-username', USER)
            time.sleep(1)
            page.fill('input#login-password', PASS)
            time.sleep(1)

            page.click('button#login-button', delay=200, force=True)

            for _ in range(40):
                page.wait_for_timeout(1000)
                if dados_capturados['blob'] and dados_capturados['challenge_id']:
                    break

            if dados_capturados['blob'] and dados_capturados['pk'] and dados_capturados['challenge_id']:
                token = solve(dados_capturados['blob'], dados_capturados['pk'], dados_capturados['surl'])

                if token:
                    print("\n[+] Enviando resposta do desafio para a API...")
                    
                    # Formata os metadados do desafio em Base64
                    metadata_raw = json.dumps({
                        "unifiedCaptchaId": dados_capturados['challenge_id'],
                        "captchaToken": token,
                        "actionType": "Generic"
                    })
                    metadata_b64 = base64.b64encode(metadata_raw.encode()).decode()

                    ataque_api_js = f"""
                    (async () => {{
                        let payload = {{
                            ctype: "Username",
                            cvalue: "{USER}",
                            password: "{PASS}"
                        }};
                        
                        let csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
                        
                        let headers = {{
                            "Content-Type": "application/json",
                            "X-CSRF-TOKEN": csrf,
                            "rblx-challenge-id": "{dados_capturados['challenge_id']}",
                            "rblx-challenge-type": "captcha",
                            "rblx-challenge-metadata": "{metadata_b64}"
                        }};
                        
                        let res = await fetch("https://auth.roblox.com/v2/login", {{
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify(payload),
                            credentials: "include"
                        }});
                        
                        if (res.status === 403 && res.headers.has('x-csrf-token')) {{
                            headers["X-CSRF-TOKEN"] = res.headers.get('x-csrf-token');
                            res = await fetch("https://auth.roblox.com/v2/login", {{
                                method: "POST",
                                headers: headers,
                                body: JSON.stringify(payload),
                                credentials: "include"
                            }});
                        }}
                        
                        return await res.json();
                    }})()
                    """
                    
                    resposta_api = page.evaluate(ataque_api_js)
                    print(f"\n[📡] RESPOSTA DO SERVIDOR: {resposta_api}")
                    
                    time.sleep(3)
                    cookies = c.cookies()
                    cookies_str = json.dumps(cookies)

                    if ".ROBLOSECURITY" in cookies_str or "twoStepVerificationData" in json.dumps(resposta_api) or "user" in resposta_api:
                        with open(COOKIE_FILE, 'w') as f:
                            json.dump(cookies, f)
                        print(f"\n✅ [SUCESSO] Sessão autenticada! Cookie salvo em: {COOKIE_FILE}")
                        b.close()
                        sys.exit(0)
                    else:
                        print("\n[-] Falha ao autenticar com o token fornecido.")

        except Exception as e:
            print(f"[-] Erro na execução: {e}")
        
        time.sleep(3)

    b.close()
    print("\n[+] Script Finalizado.")
