#!/bin/bash

# ==========================================
# 🦙 LHAMA INSTALLER - FIX CMAKE (V5.1)
# ==========================================
PASTA_IA="$HOME/Cerebro_IA"
# Usando o nome original para o wget conseguir retomar (resume) se a internet cair
MODELO_NOME="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
MODELO_URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

echo -e "\n[+] ========================================"
echo "[+] INICIANDO INSTALAÇÃO NATIVA (CMAKE + ROOT)"
echo "[+] ========================================"

su -c '
TERMUX_PID=$(pidof com.termux)
if [ -n "$TERMUX_PID" ]; then
    renice -n -20 -p $TERMUX_PID >/dev/null 2>&1
    ionice -c 1 -n 0 -p $TERMUX_PID >/dev/null 2>&1
fi
for d in /sys/devices/system/cpu/cpufreq/policy*; do 
    echo "performance" > $d/scaling_governor 2>/dev/null
done
echo "    ✅ MODO TURBO ATIVADO!"
' || true

pkg update -y
pkg install clang make cmake git wget coreutils python -y

mkdir -p "$PASTA_IA"
cd "$PASTA_IA"

# 1. Limpa a tentativa falha anterior
echo -e "\n[*] 1. Preparando o terreno..."
rm -rf llama.cpp
# Se o modelo antigo tiver menos de 1GB (quebrado), ele deleta pra baixar certo
if [ -f "llama-3.1-8b.gguf" ]; then rm "llama-3.1-8b.gguf"; fi

# 2. Baixando e Compilando com o NOVO sistema (CMake)
echo -e "\n[*] 2. Baixando código-fonte e compilando com CMake..."
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
# O novo método oficial:
cmake -B build
cmake --build build --config Release -j$(nproc)
cd ..

CORES_TOTAIS=$(nproc)
CORES_IA=$((CORES_TOTAIS - 2))
if [ "$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

# 3. Download do Cérebro (Agora com -c para continuar de onde parou se cair)
echo -e "\n[*] 3. Baixando o Cérebro da IA (4.9 GB)..."
wget -c --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "$MODELO_URL"

# 4. Criando o motor de partida
echo -e "\n[*] 4. Criando o script de ativação (ligar_ia.sh)..."
cat << START_SCRIPT > ligar_ia.sh
#!/bin/bash
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$DIR"

CORES_TOTAIS=\$(nproc)
CORES_IA=\$((CORES_TOTAIS - 2))
if [ "\$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

echo "============================================"
echo "🧠 LIGANDO A IA LOCAL - ANTI-LAG: \$CORES_IA CORES"
echo "============================================"
# O novo caminho do servidor no CMake fica dentro da pasta build/bin
./llama.cpp/build/bin/llama-server -m $MODELO_NOME -c 8192 -t \$CORES_IA --port 8080
START_SCRIPT

chmod +x ligar_ia.sh

echo -e "\n[+] ========================================"
echo "[+] ✅ LHAMA COMPILADO E INSTALADO COM SUCESSO!"
echo "[+] ========================================"
echo -e "\n👉 PARA LIGAR A IA, DIGITE:"
echo -e "cd ~/Cerebro_IA && ./ligar_ia.sh\n"

