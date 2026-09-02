#!/bin/bash

# ==========================================
# 🦙 LHAMA INSTALLER - COMPILAÇÃO NATIVA
# ==========================================
PASTA_IA="$HOME/Cerebro_IA"
MODELO_NOME="llama-3.1-8b.gguf"
MODELO_URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

echo -e "\n[+] ========================================"
echo "[+] INICIANDO INSTALAÇÃO NATIVA (ANTI-LAG)"
echo "[+] ========================================"

# 1. Instala os compiladores do Android
echo -e "\n[*] 1. Instalando compiladores e pacotes base (C/C++)..."
pkg update -y
pkg install clang make cmake git wget coreutils python -y

mkdir -p "$PASTA_IA"
cd "$PASTA_IA"

# 2. Compilando o Motor da IA
echo -e "\n[*] 2. Baixando e compilando o Llama.cpp do zero..."
echo "    -> (Isso pode levar de 1 a 3 minutos dependendo do celular)"
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp
fi
cd llama.cpp
make -j$(nproc)
cd ..

# 3. Calculando CPU para Anti-Lag
CORES_TOTAIS=$(nproc)
CORES_IA=$((CORES_TOTAIS - 3))
if [ "$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

echo -e "\n[*] 3. Configurando Anti-Lag:"
echo "    -> Seu celular tem $CORES_TOTAIS núcleos."
echo "    -> A IA usará $CORES_IA núcleos, o resto fica pro Android."

# 4. Download do Modelo Llama 3.1 8B
if [ ! -f "$MODELO_NOME" ]; then
    echo -e "\n[*] 4. Baixando o Cérebro da IA (4.9 GB). Não feche o Termux..."
    wget -O "$MODELO_NOME" "$MODELO_URL"
else
    echo -e "\n[*] 4. O modelo $MODELO_NOME já existe. Pulando download."
fi

# 5. Criando o motor de partida
echo -e "\n[*] 5. Criando o motor de partida da IA..."
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
echo -e "\n👉 PARA LIGAR A IA AGORA E SEMPRE, DIGITE:"
echo -e "cd ~/Cerebro_IA && ./ligar_ia.sh\n"

