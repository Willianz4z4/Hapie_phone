import sys
import os
import subprocess
import json
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)

# Caminho corrigido para o seu diretório atual
PASTA_TERMUX = "/data/data/com.termux/files/home/Hapie_phone/Captchas_Roblox"
os.makedirs(PASTA_TERMUX, exist_ok=True)
os.system(f"rm -f {PASTA_TERMUX}/*.jpg")

def testar_login_roblox():
    print("\n" + "="*50)
    print("🔑 AUTO-LOGIN (SISTEMA DE AUDITORIA E RESTART)")
    print("="*50 + "\n")
    
    python_script_interno = f"""
import urllib.request
import json
import time
import base64
import os
from playwright.sync_api import sync_playwright

USER_INPUT = "Willianz4z4"
PASS_INPUT = "Willianz4z4oof$$$"
NOPECHA_KEY = 'sub_1U40dzCRwBwvt6ptKgfcd8lH'

os.system('rm -f /root/*.jpg')

js_clicar_seta = '''() => {{ let el = document.querySelector("a[aria-label*='right' i], a[aria-label*='next' i], button[aria-label*='next' i], .right-arrow"); if(el) el.click(); }}'''
js_clicar_submit = '''() => {{ let els = Array.from(document.querySelectorAll("button, a")); let btn = els.find(e => e.innerText && (e.innerText.includes("Submit") || e.innerText.includes("Done"))); if(btn) btn.click(); }}'''
js_clicar_restart = '''() => {{ let els = Array.from(document.querySelectorAll("button, a, span")); let btn = els.find(e => e.innerText && (e.innerText.includes("Restart") || e.innerText.includes("Reload"))); if(btn) btn.click(); else {{ let icon = document.querySelector('.reload-icon'); if(icon) icon.click(); }} }}'''

def perguntar_pra_ia(base64_img, instrucao_texto):
    url_submit = "https://api.nopecha.com/v1/recognition/funcaptcha_match"
    payload = {{"task": instrucao_texto, "image_data": [f"data:image/jpeg;base64,{{base64_img}}"]}}
    req = urllib.request.Request(
        url_submit, data=json.dumps(payload).encode('utf-8'), 
        headers={{'Content-Type': 'application/json', 'Authorization': f'Basic {{NOPECHA_KEY}}'}}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            job_id = json.loads(response.read().decode()).get("data")
        if not job_id: return None
        time.sleep(2)
        url_retrieve = f"https://api.nopecha.com/v1/recognition/funcaptcha_match?key={{NOPECHA_KEY}}&id={{job_id}}"
        for _ in range(12):
            try:
                with urllib.request.urlopen(urllib.request.Request(url_retrieve), timeout=10) as response:
                    resultado = json.loads(response.read().decode()).get("data")
                    if resultado is not None: return resultado
            except: pass
            time.sleep(1)
    except Exception: pass
    return None

print('[Ubuntu-Python] 🚀 Iniciando Navegador...')
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-web-security'])
        context = browser.new_context(viewport={{'width': 1280, 'height': 720}})
        page = context.new_page()
        
        print('[Roblox-Bot] 🌐 Logando no Roblox...')
        page.goto('https://www.roblox.com/login', timeout=60000)
        page.wait_for_timeout(3000)
        page.fill('#login-username', USER_INPUT)
        page.fill('#login-password', PASS_INPUT)
        page.click('#login-button')
        
        print('[Roblox-Bot] 🎯 Procurando botão Start Puzzle...')
        clicou = False
        for tentativa in range(40):
            if clicou: break
            page.wait_for_timeout(2000)
            for f in page.frames:
                try:
                    btn = f.locator('button[data-theme="home.verifyButton"], button[aria-label="Start Puzzle"]').first
                    if btn.count() > 0:
                        btn.click(force=True, timeout=5000)
                        clicou = True
                        break
                except: pass
                    
        if not clicou:
            print("[Roblox-Bot] ❌ O botão Start Puzzle não apareceu.")
            page.screenshot(path='/root/00_ERRO_Sem_Botao.jpg', type="jpeg")
        else:
            print('[Roblox-Bot] ✅ Start clicado! Aguardando o Jogo...')
            page.wait_for_timeout(8000) 
            
            for fase in range(20):
                if "home" in page.url.lower():
                    print("\\n[Roblox-Bot] 🏆 VITÓRIA! Login concluído com sucesso!")
                    page.screenshot(path='/root/00_VITORIA.jpg', type="jpeg")
                    break
                    
                print(f"\\n=======================================================")
                print(f"[Roblox-Bot] ⏳ INICIANDO TENTATIVA {{fase+1}}")
                page.wait_for_timeout(3000)
                
                jogo_frame = None
                caixa_branca = None
                
                for f in page.frames:
                    if "game-core" in f.url:
                        try:
                            root_div = f.locator('#root').first
                            if root_div.count() > 0 and root_div.is_visible():
                                jogo_frame = f
                                caixa_branca = root_div
                                break
                        except: pass
                
                if not jogo_frame or not caixa_branca:
                    print(f"[Roblox-Bot] 🏁 Captcha sumiu! Vamos ver onde fomos parar...")
                    page.wait_for_timeout(4000)
                    page.screenshot(path='/root/RESULTADO_FINAL_TELA.jpg', type="jpeg")
                    break
                
                texto_pergunta = "Use the arrows to pick the image where the object directly below the claw matches the left image"
                try:
                    h2 = caixa_branca.locator('h2').first.inner_text(timeout=2000)
                    if h2: texto_pergunta = h2.replace('\\n', ' ').split(' (')[0].strip()
                except: pass
                
                match_encontrado = False
                for giro in range(16):
                    print(f"[Roblox-Bot] 📸 Giro {{giro+1}}/16...")
                    img_bytes = caixa_branca.screenshot(type="jpeg", quality=80)
                    with open(f'/root/T{{fase+1}}_Giro{{giro+1}}.jpg', 'wb') as f_img: f_img.write(img_bytes)
                        
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    resultado = perguntar_pra_ia(img_b64, texto_pergunta)
                    
                    if type(resultado) is list and len(resultado) >= 2:
                        if resultado[1] == True:
                            print(f"[Roblox-Bot] 🎯 MATCH CONFIRMADO PELA IA!")
                            caixa_branca.screenshot(path=f'/root/T{{fase+1}}_MATCH_CERTO.jpg', type="jpeg")
                            match_encontrado = True
                            break
                    try: jogo_frame.evaluate(js_clicar_seta)
                    except: pass
                    page.wait_for_timeout(1500)
                
                if match_encontrado:
                    print("[Roblox-Bot] 📤 Clicando em SUBMIT...")
                    try: jogo_frame.evaluate(js_clicar_submit)
                    except: pass
                    page.wait_for_timeout(4000)
                else:
                    print("[Roblox-Bot] 🔄 Clicando em RESTART (IA Cega)...")
                    try: jogo_frame.evaluate(js_clicar_restart)
                    except: pass
                    page.wait_for_timeout(4000)
                    continue 
                
            page.wait_for_timeout(4000)
        context.close()
        browser.close()
except Exception as e:
    print(f'[Ubuntu-Python] ⚠️ Erro crítico: {{e}}')
"""
    cmd = ["proot-distro", "login", "ubuntu", "--", "python3", "-c", python_script_interno]
    try: subprocess.run(cmd)
    except KeyboardInterrupt: pass
    
    print("\n[DEBUG-ROBLOX] 📦 Movendo fotos de dentro do Ubuntu para o Termux...")
    os.system(f"proot-distro login ubuntu -- sh -c 'cp /root/*.jpg {PASTA_TERMUX}/ 2>/dev/null'")
    
    print("\n=======================================================")
    print("📸 O SCRIPT TERMINOU. AS FOTOS ESTÃO SEGURAS NO TERMUX!")
    print("Para ver as fotos, copie e cole este comando:")
    print("cd ~/Hapie_phone/Captchas_Roblox && python3 -m http.server 8080")
    print("=======================================================\n")
    return True

if __name__ == "__main__":
    testar_login_roblox()
