#!/bin/bash

# ==========================================
# 🦙 LHAMA INSTALLER - MODO TURBO (ROOT)
# ==========================================
PASTA_IA="$HOME/Cerebro_IA"
MODELO_NOME="llama-3.1-8b.gguf"
MODELO_URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

echo -e "\n[+] ========================================"
echo "[+] INICIANDO INSTALAÇÃO NATIVA (TURBO ROOT)"
echo "[+] ========================================"

# 0. ATIVANDO MODO TURBO COM ROOT
echo -e "\n[*] 0. Solicitando permissão ROOT para destravar limite de CPU e Internet..."
su -c '
echo "    🚀 Destravando limites do Android..."
# Pega o processo principal do Termux
TERMUX_PID=$(pidof com.termux)

if [ -n "$TERMUX_PID" ]; then
    # Prioridade máxima de Processamento
    renice -n -20 -p $TERMUX_PID >/dev/null 2>&1
    # Prioridade máxima de Internet e Leitura de Disco
    ionice -c 1 -n 0 -p $TERMUX_PID >/dev/null 2>&1
fi

# Força todos os núcleos do celular a rodarem no clock MÁXIMO
for d in /sys/devices/system/cpu/cpufreq/policy*; do 
    echo "performance" > $d/scaling_governor 2>/dev/null
done
echo "    ✅ MODO TURBO ATIVADO! (Termux com 100% de prioridade)"
' || echo "    [-] Aviso: Root negado ou não encontrado. Continuando em velocidade normal."

# 1. Instala os compiladores do Android
echo -e "\n[*] 1. Instalando compiladores e pacotes base (C/C++)..."
pkg update -y
pkg install clang make cmake git wget coreutils python -y

mkdir -p "$PASTA_IA"
cd "$PASTA_IA"

# 2. Compilando o Motor da IA
echo -e "\n[*] 2. Compilando o motor da IA na velocidade da luz (Todos os núcleos)..."
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp
fi
cd llama.cpp
# Usa o máximo de threads disponíveis para compilar rápido
make -j$(nproc)
cd ..

# 3. Calculando CPU para Anti-Lag (Na hora de rodar o jogo)
CORES_TOTAIS=$(nproc)
CORES_IA=$((CORES_TOTAIS - 3))
if [ "$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

echo -e "\n[*] 3. Configurando Anti-Lag para quando a IA for ligada:"
echo "    -> Seu celular tem $CORES_TOTAIS núcleos."
echo "    -> Durante o jogo, a IA usará $CORES_IA núcleos para não travar o Roblox."

# 4. Download do Modelo Llama 3.1 8B
if [ ! -f "$MODELO_NOME" ]; then
    echo -e "\n[*] 4. Baixando o Cérebro da IA (4.9 GB). Focando banda de internet..."
    # Aumentando limite de retries e timeout do wget para conexões instáveis
    wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 -O "$MODELO_NOME" "$MODELO_URL"
else
    echo -e "\n[*] 4. O modelo $MODELO_NOME já existe. Pulando download."
fi

# 5. Criando o motor de partida
echo -e "\n[*] 5. Criando o script de ativação (ligar_ia.sh)..."
cat << START_SCRIPT > ligar_ia.sh
#!/bin/bash
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$DIR"

CORES_TOTAIS=\$(nproc)
CORES_IA=\$((CORES_TOTAIS - 3))
if [ "\$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

echo "============================================"
echo "🧠 LIGANDO A IA LOCAL - ANTI-LAG: \$CORES_IA CORES"
echo "============================================"
./llama.cpp/llama-server -m $MODELO_NOME -c 8192 -t \$CORES_IA --port 8080
START_SCRIPT

chmod +x ligar_ia.sh

echo -e "\n[+] ========================================"
echo "[+] ✅ LHAMA COMPILADO E INSTALADO COM SUCESSO!"
echo "[+] ========================================"
echo -e "\n👉 PARA LIGAR A IA, DIGITE:"
echo -e "cd ~/Cerebro_IA && ./ligar_ia.sh\n"

