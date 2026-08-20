import os
import shutil
import subprocess
import sys
import zlib
import base64

# Pastas Corretas
dev_dir = os.path.expanduser("~/Hapie_phone-dev")
pub_dir = os.path.expanduser("~/Hapie_phone")

def ofuscar_codigo(codigo_fonte):
    codigo_cripto = base64.b64encode(zlib.compress(codigo_fonte.encode('utf-8'))).decode('utf-8')
    return f'import zlib,base64\nexec(zlib.decompress(base64.b64decode(b"{codigo_cripto}")).decode("utf-8"))'

def compilar_para_binario(caminho_origem, caminho_destino_dir, nome_arquivo):
    nome_base = nome_arquivo.replace(".py", "")
    caminho_so = os.path.join(caminho_destino_dir, nome_base + ".so")
    caminho_py_temp = os.path.join(caminho_destino_dir, nome_arquivo)

    if os.path.exists(caminho_so) and os.path.getmtime(caminho_origem) <= os.path.getmtime(caminho_so):
        return False

    print(f"⚙️ Compilando (Novo/Alterado): {nome_arquivo}")
    shutil.copy2(caminho_origem, caminho_py_temp)
    
    cwd_original = os.getcwd()
    os.chdir(caminho_destino_dir)
    try:
        subprocess.run([sys.executable, "-m", "cython", "-3", nome_arquivo], check=True, stdout=subprocess.DEVNULL)
        include_path = os.path.join(sys.prefix, "include/python" + sys.version[:4])
        cmd = ["gcc", "-shared", "-fPIC", "-I" + include_path, "-o", nome_base + ".so", nome_base + ".c"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        os.remove(nome_arquivo)
        if os.path.exists(nome_base + ".c"): os.remove(nome_base + ".c")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao compilar {nome_arquivo}: {e}")
        return False
    finally:
        os.chdir(cwd_original)

def arquivos_diferentes(arq1, arq2):
    if not os.path.exists(arq2): return True
    with open(arq1, 'rb') as f1, open(arq2, 'rb') as f2:
        return f1.read() != f2.read()

print("🚀 INICIANDO PREPARAÇÃO (DELTA SYNC)...\n")

if not os.path.exists(pub_dir):
    os.makedirs(pub_dir, exist_ok=True)

arquivos_modificados = []

for root, dirs, files in os.walk(dev_dir):
    pasta_rel = os.path.relpath(root, dev_dir)
    if any(i in pasta_rel for i in [".git", "__pycache__"]): continue
    
    destino = os.path.join(pub_dir, pasta_rel) if pasta_rel != "." else pub_dir
    os.makedirs(destino, exist_ok=True)
    
    for file in files:
        if file.endswith((".log", ".png", ".tmp", ".so", ".git")): continue
        if file == "preparar_publica.py": continue 
        
        origem = os.path.join(root, file)
        copia = os.path.join(destino, file)

        if file == "phone_assistance.py":
            if compilar_para_binario(origem, destino, file):
                arquivos_modificados.append(f"⚙️ {file} (Compilado para .so)")
                
        elif file.endswith(".py") and "Roblox" not in root:
            with open(origem, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            conteudo_ofuscado = ofuscar_codigo(conteudo)
            
            precisa_atualizar = True
            if os.path.exists(copia):
                with open(copia, "r", encoding="utf-8") as f:
                    if f.read() == conteudo_ofuscado:
                        precisa_atualizar = False
                        
            if precisa_atualizar:
                with open(copia, "w", encoding="utf-8") as f:
                    f.write(conteudo_ofuscado)
                arquivos_modificados.append(f"🔒 {file} (Ofuscado)")
                
        else:
            if arquivos_diferentes(origem, copia):
                shutil.copy2(origem, copia)
                arquivos_modificados.append(f"📄 {file} (Copiado)")

print("\n📊 RESUMO DAS MODIFICAÇÕES:")
if not arquivos_modificados:
    print(" ✅ Nenhuma alteração nova detectada. Código já está idêntico.")
else:
    for arq in arquivos_modificados:
        print(f"  {arq}")

print("\n🌐 Sincronizando com GitHub...")
modo_automatico = len(sys.argv) > 1 and sys.argv[1] == "ADM"

# --- TRAVA DE SEGURANÇA DO GIT ---
if not os.path.exists(os.path.join(pub_dir, ".git")):
    print("❌ ERRO: A pasta Hapie_phone não é um repositório Git!")
    print("➡️ Vá no terminal e digite: cd ~/Hapie_phone && git init")
    sys.exit(1)

try:
    os.chdir(pub_dir) 
    subprocess.run(["git", "add", "-A"], check=True)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    
    if status.stdout.strip():
        msg_commit = "Autoupdate via auto_github" if modo_automatico else "Update manual público"
        subprocess.run(["git", "commit", "-m", msg_commit], check=True)
        subprocess.run(["git", "push"], check=True)
        print("\n✅ Enviado para o GitHub com sucesso!")
    else:
        print("\n⚠️ O Git confirmou: Nenhuma alteração pendente para comitar.")
except Exception as e:
    print(f"\n❌ Erro no Git: {e}")

print("\n✅ PREPARAÇÃO CONCLUÍDA!")
