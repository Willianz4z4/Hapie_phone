import cv2
import pytesseract
from pytesseract import Output
import re
import time
import os
import random
import json
import sqlite3
import urllib.request
import difflib

ROBLOX_TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Data", "Roblox_token.json")
MIN_TOKEN_LENGTH = 500

TERMOS_DESLOGADO = [
    "saiu", "sign out", "log out", "salir", "cerrar",
    "déconnexion", "abmelden", "keluar", "выйти", "çıkış", "đăng xuất"
]

# ==========================================
# 1. FUNÇÕES DE EXTRAÇÃO DE TOKEN
# ==========================================
def get_roblox_username(token):
    try:
        req = urllib.request.Request(
            "https://users.roblox.com/v1/users/authenticated",
            headers={
                "Cookie": f".ROBLOSECURITY={token}",
                "User-Agent": "Roblox/WinInet"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("name")
    except Exception:
        return None

def extract_all_package_tokens(pkg):
    locais_db = [
        f"/data/data/{pkg}/app_webview/Default/Cookies",
        f"/data/data/{pkg}/app_webview/Default/Network/Cookies"
    ]

    tokens_encontrados = []

    for db_origem in locais_db:
        db_temp = f"/data/data/com.termux/files/home/temp_cookie_{pkg}.db"
        try:
            subprocess_cmd = f"su -c 'cp {db_origem} {db_temp} && chmod 777 {db_temp}'"
            os.system(subprocess_cmd)
        except Exception:
            continue

        if os.path.exists(db_temp):
            try:
                conn = sqlite3.connect(db_temp)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cookies WHERE name='.ROBLOSECURITY'")
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    if row and row[0] and "_|WARNING" in row[0] and len(row[0]) >= MIN_TOKEN_LENGTH:
                        if row[0] not in tokens_encontrados:
                            tokens_encontrados.append(row[0])
            except Exception:
                pass
            finally:
                if os.path.exists(db_temp):
                    os.remove(db_temp)

    return tokens_encontrados

def salvar_token_direto(pkg, token):
    username = get_roblox_username(token)
    if not username:
        return None

    try:
        dados_salvos = {}
        if os.path.exists(ROBLOX_TOKEN_FILE):
            with open(ROBLOX_TOKEN_FILE, 'r', encoding='utf-8') as f:
                dados_salvos = json.load(f)

        if pkg not in dados_salvos:
            dados_salvos[pkg] = {}

        token_anterior = dados_salvos[pkg].get(username, "")
        if token != token_anterior:
            dados_salvos[pkg][username] = token
            with open(ROBLOX_TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(dados_salvos, f, indent=4, ensure_ascii=False)
            print(f"[+] [TOKEN CAPTURADO] Conta salva com sucesso: @{username}")
            return username
    except Exception as e:
        print(f"[-] Erro ao salvar token no JSON: {e}")

    return username


# ==========================================
# 2. MOTOR DE FULLSCREEN INTELIGENTE
# ==========================================
def aplicar_fullscreen_se_fluido(pacote):
    shared_prefs_path = f"/data/data/{pacote}/shared_prefs"
    check_cmd = f"su -c '[ -d \"{shared_prefs_path}\" ] && [ \"$(ls -A {shared_prefs_path} 2>/dev/null)\" ] && echo \"True\" || echo \"False\"'"
    resultado = os.popen(check_cmd).read().strip()
    
    print(f"[*] [CLONE CHECK] Analisando '{pacote}' | É flutuante? -> {resultado}", flush=True)
    
    if resultado == "True":
        print(f"[+] [FLOATING DETECTED] O app '{pacote}' é flutuante. Aplicando layout otimizado...", flush=True)
        
        res_cmd = "su -c 'wm size' | grep -oE '[0-9]+x[0-9]+' | head -n 1"
        res = os.popen(res_cmd).read().strip()
        if not res:
            w, h = 720, 1280
        else:
            w, h = map(int, res.split('x'))
            
        bar_height = 85
        new_h = h - bar_height
        
        script_sh = f"""#!/bin/sh
for dir in "/data/data/{pacote}" "/sdcard/Android/data/{pacote}"; do
    if [ -d "$dir" ]; then
        pref_dir="$dir/shared_prefs"
        mkdir -p "$pref_dir" 2>/dev/null
        
        for name in "{pacote}_preferences.xml" "FreeFormWindow.xml" "freeform.xml"; do
            target="$pref_dir/$name"
            chmod 666 "$target" 2>/dev/null
            cat << 'XML_EOF' > "$target"
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <int name='free_form_window_left' value='0' />
    <int name='free_form_window_top' value='{bar_height}' />
    <int name='free_form_window_right' value='{w}' />
    <int name='free_form_window_bottom' value='{h}' />
    <int name='free_form_window_width' value='{w}' />
    <int name='free_form_window_height' value='{new_h}' />
    <int name='app_cloner_current_window_left' value='0' />
    <int name='app_cloner_current_window_top' value='{bar_height}' />
    <int name='app_cloner_current_window_right' value='{w}' />
    <int name='app_cloner_current_window_bottom' value='{h}' />
</map>
XML_EOF
            chmod 666 "$target" 2>/dev/null
            OWNER=$(stat -c "%u:%g" "$dir" 2>/dev/null)
            if [ -n "$OWNER" ]; then
                chown "$OWNER" "$target" 2>/dev/null
            fi
        done
    fi
done
"""
        script_path = os.path.join(os.getcwd(), "temp_fullscreen.sh")
        with open(script_path, "w") as f:
            f.write(script_sh)
            
        os.system(f"su -c 'sh {script_path}'")
        if os.path.exists(script_path):
            os.remove(script_path)
            
        print(f"[+] [FULLSCREEN] Aplicado com sucesso em '{pacote}'!", flush=True)
    else:
        print(f"[-] [STANDARD] O app '{pacote}' NÃO é flutuante. Abrindo normalmente.", flush=True)


# ==========================================
# 3. MOTOR DE EXECUÇÃO
# ==========================================
def chegar_na_tela_de_decisao(pacote):
    print(f"\n[*] [MOTOR] Matando '{pacote}' preventivamente para evitar bugs (Clean Start)...")
    os.system(f'su -c "am force-stop {pacote}"')
    time.sleep(2)

    aplicar_fullscreen_se_fluido(pacote)

    print(f"[*] [MOTOR] Abrindo '{pacote}'...")
    os.system(f'su -c "monkey -p {pacote} 1" > /dev/null 2>&1')
    
    print(f"[*] [MOTOR] Verificando se o app realmente abriu...")
    app_aberto = False
    for _ in range(15): # Aguarda até 15 segundos pela confirmação
        check_pid = os.popen(f"su -c 'pidof {pacote}'").read().strip()
        if check_pid:
            print(f"[+] [MOTOR] Confirmado! O app '{pacote}' está rodando (PID: {check_pid}).")
            app_aberto = True
            break
        time.sleep(1)

    if not app_aberto:
        print(f"[-] [AVISO] O app '{pacote}' falhou ao abrir ou crashou! Dando um empurrão final...")
        os.system(f'su -c "monkey -p {pacote} 1" > /dev/null 2>&1')
        time.sleep(3)

    print("[*] [MOTOR] Jogo na tela. Iniciando o roteiro calibrado...")

    acoes = [
        {"num": 1, "tipo": "clique", "x": 64, "y": 145, "espera": 9.0},
        {"num": 2, "tipo": "scroll", "x1": 375, "y1": 885, "x2": 565, "y2": 124, "duracao_ms": 155, "espera": 1.5},
        {"num": 3, "tipo": "clique", "x": 458, "y": 857, "espera": 1.35}
    ]

    for acao in acoes:
        tempo = random.uniform(acao["espera"] * 0.95, acao["espera"] * 1.05)
        time.sleep(tempo)
        
        if acao["tipo"] == "clique":
            x = acao["x"] + random.randint(-2, 2)
            y = acao["y"] + random.randint(-2, 2)
            os.system(f"su -c 'input tap {x} {y}'")
            print(f"  -> [Ação {acao['num']}] Clique aplicado em X:{x} Y:{y}")
            
        elif acao["tipo"] == "scroll":
            duracao = acao["duracao_ms"] + random.randint(-10, 10)
            os.system(f"su -c 'input swipe {acao['x1']} {acao['y1']} {acao['x2']} {acao['y2']} {duracao}'")
            print(f"  -> [Ação {acao['num']}] Scroll aplicado perfeitamente!")

    print("[+] [MOTOR] Chegamos na tela de contas!")
    time.sleep(2)


# ==========================================
# 4. MOTOR DE VISÃO
# ==========================================
def scan_unico(caminho_imagem):
    os.system(f'su -c "screencap -p {caminho_imagem}"')
    imagem = cv2.imread(caminho_imagem)
    if imagem is None: return {}

    largura_img = imagem.shape[1]
    imagem_ampliada = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    imagem_cinza = cv2.cvtColor(imagem_ampliada, cv2.COLOR_BGR2GRAY)
    dados = pytesseract.image_to_data(imagem_cinza, config=r'--psm 11', output_type=Output.DICT)

    nicks_encontrados = []
    linhas_deslogadas = []

    for i in range(len(dados['text'])):
        texto = dados['text'][i].strip().lower()
        if not texto: continue

        x_real = int(dados['left'][i] / 2)
        y_real = int(dados['top'][i] / 2)

        if x_real > (largura_img * 0.5):
            for termo in TERMOS_DESLOGADO:
                if termo in texto:
                    linhas_deslogadas.append(y_real)
                    break

        match = re.search(r'@([a-zA-Z0-9_]{3,20})', dados['text'][i].strip())
        if match:
            nick = match.group(1)
            nicks_encontrados.append({"nick": nick, "y": y_real, "x": 350})

    contas_validas = {}

    for item in nicks_encontrados:
        nick = item["nick"]
        y_nick = item["y"]

        esta_deslogada = False
        for y_d in linhas_deslogadas:
            if abs(y_nick - y_d) < 45:
                esta_deslogada = True
                break

        if not esta_deslogada:
            contas_validas[nick] = {"y": y_nick, "x": item["x"]}

    return contas_validas

def rodar_radar():
    caminho_temp = f"/sdcard/tela_scan_radar.png"
    contas_encontradas = scan_unico(caminho_temp)
    if os.path.exists(caminho_temp): os.remove(caminho_temp)
    return contas_encontradas


# ==========================================
# 5. FUNÇÃO FOCUS INTELIGENTE
# ==========================================
def account_focus(alvo_nick):
    print(f"\n=======================================")
    print(f" 🎯 [FOCUS] Consultando token para: @{alvo_nick}")
    print(f"=======================================")

    pkg_alvo = None
    json_modificado = False

    if os.path.exists(ROBLOX_TOKEN_FILE):
        try:
            with open(ROBLOX_TOKEN_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            pacotes_para_verificar = list(dados.keys())

            for pkg in pacotes_para_verificar:
                contas_do_pkg = dados[pkg]
                
                check_install = os.popen(f"su -c 'pm path {pkg}'").read().strip()
                
                if not check_install:
                    print(f"[-] [AUTOLIMPEZA] O pacote '{pkg}' não está instalado. Removendo do JSON...")
                    del dados[pkg]
                    json_modificado = True
                    continue

                for nick_salvo in contas_do_pkg.keys():
                    if nick_salvo.lower() == alvo_nick.lower():
                        pkg_alvo = pkg
                        alvo_nick = nick_salvo
                        break
                if pkg_alvo:
                    break

            if json_modificado:
                with open(ROBLOX_TOKEN_FILE, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, indent=4, ensure_ascii=False)
                print("[+] [AUTOLIMPEZA] Arquivo JSON limpo e salvo com sucesso!")

        except Exception as e:
            print(f"[-] Erro ao processar o JSON de tokens: {e}")

    if not pkg_alvo:
        print(f"[-] [FOCUS ABORTADO] O nick '@{alvo_nick}' não tem token válido em nenhum app instalado.")
        return False

    print(f"[+] [FOCUS] Token encontrado e app verificado! Pacote ativo: {pkg_alvo}")

    chegar_na_tela_de_decisao(pkg_alvo)
    contas_na_tela = rodar_radar()

    if not contas_na_tela:
        print("[-] Nenhuma conta ativa encontrada na tela.")
        os.system(f'su -c "am force-stop {pkg_alvo}"')
        return False

    nicks_disponiveis = list(contas_na_tela.keys())
    alvo_encontrado = None

    for n in nicks_disponiveis:
        if n.lower() == alvo_nick.lower():
            alvo_encontrado = n
            break

    if not alvo_encontrado:
        matches = difflib.get_close_matches(alvo_nick, nicks_disponiveis, n=1, cutoff=0.4)
        if matches:
            alvo_encontrado = matches[0]

    if alvo_encontrado:
        coord = contas_na_tela[alvo_encontrado]
        print(f"[+] Conta localizada na tela: '@{alvo_encontrado}'. Focando (clicando)...")
        os.system(f"su -c 'input tap {coord['x']} {coord['y']}'")
        print("[⏳] Aguardando 5 segundos para o login focar...")
        time.sleep(5)
    else:
        print(f"[-] A conta '@{alvo_nick}' está salva no JSON, mas não apareceu visível na tela de troca.")

    print(f"[💀] Fechando o app '{pkg_alvo}'...")
    os.system(f'su -c "am force-stop {pkg_alvo}"')
    return True


# ==========================================
# 6. AUDITORIA GERAL (MAPEADOR GLOBAL)
# ==========================================
def obter_contas_salvas_no_json(pacote):
    try:
        if os.path.exists(ROBLOX_TOKEN_FILE):
            with open(ROBLOX_TOKEN_FILE, 'r', encoding='utf-8') as f:
                tokens = json.load(f)
                return list(tokens.get(pacote, {}).keys())
    except: pass
    return []

def audit_package(pacote):
    print(f"\n=======================================")
    print(f" 🔄 INICIANDO AUDITORIA INTELIGENTE: {pacote}")
    print(f"=======================================")

    tokens_no_banco = extract_all_package_tokens(pacote)
    if not tokens_no_banco:
        print(f"[-] REGRA DE PULO: O app '{pacote}' não possui tokens engatilhados.")
        print("[-] Nenhuma conta está logada neste app. Pulando para o próximo...")
        return

    print(f"[+] '{pacote}' possui {len(tokens_no_banco)} token(s) no banco de dados. Iniciando varredura visual...")

    while True:
        chegar_na_tela_de_decisao(pacote)
        contas_na_tela = rodar_radar()

        if not contas_na_tela:
            print("[-] Nenhuma conta ativa lida pelo OCR nesta tela. Encerrando auditoria.")
            break

        salvas = obter_contas_salvas_no_json(pacote)
        faltando = [nick for nick in contas_na_tela.keys() if nick not in salvas]

        print(f"\n[📊 STATUS DA TELA (Filtrado)]")
        print(f"Contas ativas válidas na tela: {len(contas_na_tela)}")
        print(f"Total já salvas: {len(salvas)}")
        print(f"Faltam capturar: {len(faltando)}")

        if not faltando:
            print("\n[✅] TODAS AS CONTAS VÁLIDAS DESTA TELA JÁ ESTÃO SALVAS!")
            os.system(f'su -c "am force-stop {pacote}"')
            break

        alvo = faltando[0]
        coord = contas_na_tela[alvo]
        print(f"\n[🎯 AÇÃO] A conta ativa '@{alvo}' não tem token salvo! Clicando nela...")

        os.system(f"su -c 'input tap {coord['x']} {coord['y']}'")
        print("[⏳] Monitorando banco de dados para capturar o token (máx 15s)...")

        capturado = False
        for _ in range(15):
            time.sleep(1)
            tokens_atuais = extract_all_package_tokens(pacote)
            for t in tokens_atuais:
                username_salvo = salvar_token_direto(pacote, t)
                if username_salvo and username_salvo.lower() == alvo.lower():
                    capturado = True
                    break
            if capturado:
                break

        if capturado:
            print(f"[✨] Token da conta '@{alvo}' capturado com sucesso!")
        else:
            print(f"[-] Aviso: O token de '@{alvo}' não apareceu a tempo, prosseguindo...")

        print("[💀] Fechando o app. Reiniciando o loop...")
        os.system(f'su -c "am force-stop {pacote}"')
        time.sleep(2)


def audit_all_roblox():
    print("\n=======================================")
    print(" 🌍 INICIANDO AUDITORIA GLOBAL EM TODOS OS ROBLOX")
    print("=======================================")
    
    pacotes_raw = os.popen("su -c 'pm list packages | grep roblox'").read().strip()
    pacotes = [p.replace("package:", "") for p in pacotes_raw.split("\n") if p]
    
    if not pacotes:
        print("[-] Nenhum aplicativo Roblox encontrado no celular.")
        return

    print(f"[+] Foram encontrados {len(pacotes)} aplicativos Roblox instalados!")
    
    for i, pkg in enumerate(pacotes, 1):
        print(f"\n---> [{i}/{len(pacotes)}] Analisando pacote: {pkg} <---")
        audit_package(pkg)
        
    print("\n=======================================")
    print(" ✅ AUDITORIA GLOBAL CONCLUÍDA COM SUCESSO!")
    print("=======================================")


if __name__ == "__main__":
    audit_all_roblox()

