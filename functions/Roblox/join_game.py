import os
import sys
import subprocess
import json
import re

# ========================================================
# ⚙️ CONFIGURAÇÃO DO BANCO DE DADOS
# ========================================================
ARQUIVO_JSON = os.path.expanduser("~/Hapie_phone/Data/Roblox_token.json")

def executar(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    if len(sys.argv) < 3:
        print("❌ Uso correto: python join_game.py <NICK> <LINK_DO_JOGO>")
        print("Exemplo: python join_game.py gwysysysu \"https://www.roblox.com/games/12345?privateServerLinkCode=XYZ\"")
        sys.exit(1)

    nick_alvo = sys.argv[1]
    link_jogo = sys.argv[2]

    print(f"🎮 Procurando a conta: {nick_alvo}")

    # ========================================================
    # 1. LER O JSON E ACHAR QUAL O PACOTE DA CONTA
    # ========================================================
    if not os.path.exists(ARQUIVO_JSON):
        print(f"❌ Arquivo de banco de dados não encontrado em: {ARQUIVO_JSON}")
        sys.exit(1)

    try:
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            banco_dados = json.load(f)
    except json.JSONDecodeError:
        print("❌ Erro ao ler o arquivo JSON. O formato pode estar quebrado.")
        sys.exit(1)

    pacote_encontrado = None

    for nome_pacote, contas in banco_dados.items():
        if nick_alvo in contas:
            pacote_encontrado = nome_pacote
            break

    if not pacote_encontrado:
        print(f"❌ Conta '{nick_alvo}' não encontrada no Roblox_token.json.")
        sys.exit(1)

    print(f"✅ Conta localizada! Ela pertence ao pacote: {pacote_encontrado}")

    # ========================================================
    # 2. CONVERTER LINK DA WEB PARA DEEP LINK (AUTO-JOIN)
    # ========================================================
    # Transforma "https://..." em "roblox://placeId=..." para pular a tela de Play
    deep_link = link_jogo
    place_id_match = re.search(r'/games/(\d+)', link_jogo)
    
    if place_id_match:
        place_id = place_id_match.group(1)
        deep_link = f"roblox://placeId={place_id}"
        
        # Se for um link de servidor VIP, a gente gruda o código no Deep Link também
        vip_match = re.search(r'privateServerLinkCode=([^&]+)', link_jogo)
        if vip_match:
            deep_link += f"&privateServerLinkCode={vip_match.group(1)}"
            
    print(f"🔗 Link convertido para auto-join: {deep_link}")

    # ========================================================
    # 3. LANÇAR O JOGO DIRETO NO SERVIDOR
    # ========================================================
    print(f"🚀 Forçando a entrada no jogo...")
    
    # Passamos o deep_link gerado em vez do link web
    cmd_abrir = f'su -c "am start -W -a android.intent.action.VIEW -d \\"{deep_link}\\" {pacote_encontrado}"'
    
    res = executar(cmd_abrir)

    if "Error:" in res.stderr or "Error:" in res.stdout:
        print(f"❌ Erro ao tentar abrir o jogo via Intent.\nDetalhes: {res.stderr}")
    else:
        print("✅ Comando enviado com sucesso! O jogo deve iniciar a tela de loading automaticamente agora.")

if __name__ == "__main__":
    main()
