import time, json, requests, os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# CONFIGURAÇÕES
CAPMONSTER_KEY = "35e32346fa20ab9dfa29b14e7809de2d"
PASTA_FOTOS = "/data/data/com.termux/files/home/Hapie_phone/Captchas_Roblox"
USER = "Alaquelegalz4"
PASS = "willianz4z4oof$"
PK_ROBLOX = "476068BF-9607-4799-B53D-366BE98E2B84"

def resolver_captcha_na_nuvem(pk):
    task = {
        "clientKey": CAPMONSTER_KEY,
        "task": {
            "type": "FunCaptchaTaskProxyless",
            "websiteURL": "https://www.roblox.com/login",
            "websitePublicKey": pk
        }
    }
    print("[CapMonster] Criando tarefa...")
    try:
        tid = requests.post("https://api.capmonster.cloud/createTask", json=task).json().get("taskId")
        print(f"[CapMonster] Aguardando solução (ID: {tid})...")
        while True:
            time.sleep(3)
            res = requests.post("https://api.capmonster.cloud/getTaskResult", json={"clientKey": CAPMONSTER_KEY, "taskId": tid}).json()
            if res.get("status") == "ready":
                return res["solution"]["token"]
            elif res.get("status") == "failed":
                return None
    except Exception as e:
        print(f"[CapMonster] Erro: {e}")
        return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        stealth_sync(page)
        
        print("[1] Acessando Roblox...")
        page.goto("https://www.roblox.com/login")
        
        print("[2] Inserindo credenciais...")
        page.fill("#login-username", USER)
        page.fill("#login-password", PASS)
        page.click("#login-button")
        
        time.sleep(5)
        page.screenshot(path=f"{PASTA_FOTOS}/tela_pre_captcha.jpg")
        
        print("[3] Enviando Captcha para nuvem...")
        token = resolver_captcha_na_nuvem(PK_ROBLOX)
        
        if token:
            print("[4] Injetando Token de Sucesso...")
            page.evaluate(f"window.parent.postMessage(JSON.stringify({{eventId: 'challenge-complete', payload: {{ sessionToken: '{token}' }}}}), '*');")
            time.sleep(2)
            page.click("#login-button")
            time.sleep(8)
            
            page.screenshot(path=f"{PASTA_FOTOS}/resultado_final.jpg")
            print(f"URL Final: {page.url}")
            
            if "home" in page.url or "dashboard" in page.url:
                print("🎉 SUCESSO! O Stealth enganou o Arkose!")
            else:
                print("❌ Não logou. Verifique a foto 'resultado_final.jpg' nos Downloads.")
        else:
            print("❌ Falha ao resolver Captcha.")
        
        browser.close()

if __name__ == "__main__":
    main()
