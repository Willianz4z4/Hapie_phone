#!/bin/bash

# ==========================================
# 🦙 LHAMA INSTALLER - ISOLADO E ANTI-LAG
# ==========================================
PASTA_IA="$HOME/Cerebro_IA"
MODELO_NOME="llama-3.1-8b.gguf"
MODELO_URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

echo -e "\n[+] ========================================"
echo "[+] INICIANDO INSTALAÇÃO DO AMBIENTE ISOLADO"
echo "[+] ========================================"

# 1. Atualiza e instala ferramentas essenciais
echo -e "\n[*] 1. Baixando pacotes base do Termux..."
pkg update -y && pkg upgrade -y
pkg install python wget git llama.cpp nproc -y

# 2. Criação do Ambiente Separado
echo -e "\n[*] 2. Criando o sandbox da IA em $PASTA_IA..."
mkdir -p "$PASTA_IA"
cd "$PASTA_IA"

# 3. Cria Ambiente Virtual Python (Isolamento total)
echo -e "\n[*] 3. Criando bolha Python (Virtual Environment)..."
python -m venv venv_lhama

# 4. Cálculo Inteligente de CPU (Anti-Lag)
CORES_TOTAIS=$(nproc)
CORES_IA=$((CORES_TOTAIS - 3))
if [ "$CORES_IA" -lt 2 ]; then
    CORES_IA=2
fi
echo -e "\n[*] 4. Configurando Anti-Lag:"
echo "    -> Seu celular tem $CORES_TOTAIS núcleos."
echo "    -> A IA usará $CORES_IA núcleos."
echo "    -> O Android ficará com o resto para evitar travamentos."

# 5. Download do Modelo Llama 3.1 8B (Q4_K_M - Melhor Custo Benefício)
if [ ! -f "$PASTA_IA/$MODELO_NOME" ]; then
    echo -e "\n[*] 5. Baixando o Cérebro da IA (4.9 GB). Isso pode demorar, não feche o Termux..."
    wget -O "$MODELO_NOME" "$MODELO_URL"
else
    echo -e "\n[*] 5. O modelo $MODELO_NOME já existe. Pulando download."
fi

# 6. Criação do Script de Inicialização da IA
echo -e "\n[*] 6. Criando o motor de partida da IA..."
cat << 'START_SCRIPT' > ligar_ia.sh
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

CORES_TOTAIS=$(nproc)
CORES_IA=$((CORES_TOTAIS - 3))
if [ "$CORES_IA" -lt 2 ]; then CORES_IA=2; fi

echo "============================================"
echo "🧠 LIGANDO A INTELIGÊNCIA ARTIFICIAL LOCAL"
echo "============================================"
echo "[-] Proteção Anti-Lag: ON ($CORES_IA Threads)"
echo "[-] Contexto: 8192 (Alto Desempenho)"
echo "[-] Aguardando o Hapiephone..."
echo "============================================"

# Ativa a bolha Python
source venv_lhama/bin/activate

# Roda o Llama-server nativo do Termux limitando as Threads (-t)
llama-server -m llama-3.1-8b.gguf -c 8192 -t $CORES_IA --port 8080
START_SCRIPT

chmod +x ligar_ia.sh

echo -e "\n[+] ========================================"
echo "[+] ✅ LHAMA INSTALADO COM SUCESSO!"
echo "[+] O ambiente foi isolado na pasta: Cerebro_IA"
echo "[+] ========================================"
echo -e "\n👉 PARA LIGAR A IA AGORA E SEMPRE, DIGITE:"
echo -e "cd ~/Cerebro_IA && ./ligar_ia.sh\n"

