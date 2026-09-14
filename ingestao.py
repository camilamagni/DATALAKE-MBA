import boto3
import sys
import os

from botocore.exceptions import ClientError
from datetime import datetime


# ============================================================
# CARREGAR CREDENCIAIS DO ARQUIVO
# ============================================================

def carregar_credenciais(caminhos_possiveis=["AWS_CREDENTIAL.env", "AWS_CREDENTIAL"]):
    caminho_encontrado = None
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            caminho_encontrado = caminho
            break

    if not caminho_encontrado:
        print(f"\nERRO: Nenhum arquivo de credenciais encontrado ({', '.join(caminhos_possiveis)}).")
        sys.exit(1)

    credenciais = {}
    with open(caminho_encontrado, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                credenciais[chave.strip()] = valor.strip().strip('"').strip("'")

    chaves_obrigatorias = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for chave in chaves_obrigatorias:
        if chave not in credenciais:
            print(f"\nERRO: Chave '{chave}' ausente no arquivo '{caminho_encontrado}'.")
            sys.exit(1)

    return credenciais


CREDS = carregar_credenciais()

AWS_ACCESS_KEY_ID = CREDS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = CREDS["AWS_SECRET_ACCESS_KEY"]
AWS_SESSION_TOKEN = CREDS.get("AWS_SESSION_TOKEN")
AWS_REGION = CREDS["AWS_REGION"]


# ============================================================
# ARGUMENTO
# ============================================================

if len(sys.argv) != 2:
    print()
    print("Uso:")
    print("    python ingestao.py NOME_DO_BUCKET")
    print()
    print("Exemplo:")
    print("    python ingestao.py datalake-turma-01-aluno-9999")
    print()
    sys.exit(1)

BUCKET_NAME = sys.argv[1]


# ============================================================
# CONEXÃO COM S3
# ============================================================

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)


# ============================================================
# DATA DE INGESTÃO
# ============================================================

DATA_INGESTAO = datetime.now().strftime("%Y-%m-%d")


# ============================================================
# CONFIGURAÇÃO DOS ARQUIVOS
# ============================================================

ARQUIVOS = {
    "pedidos.csv": {
        "origem": "Dados/pedidos.csv",
        "destino": f"raw/pedidos/ingest_date={DATA_INGESTAO}/pedidos.csv"
    },
    "clientes.csv": {
        "origem": "Dados/clientes.csv",
        "destino": f"raw/clientes/ingest_date={DATA_INGESTAO}/clientes.csv"
    },
    "produtos.csv": {
        "origem": "Dados/produtos.csv",
        "destino": f"raw/produtos/ingest_date={DATA_INGESTAO}/produtos.csv"
    }
}


# ============================================================
# TESTAR CONEXÃO
# ============================================================

def testar_conexao():
    print("\nTestando conexão com AWS...")
    try:
        s3.head_bucket(
            Bucket=BUCKET_NAME
        )
        print("Bucket encontrado!")
        return True
    except ClientError as e:
        print("Erro ao acessar o bucket:")
        print(e)
        return False


# ============================================================
# ENVIAR ARQUIVO
# ============================================================

def enviar_arquivo(nome, origem, destino):
    print()
    print(f"Arquivo : {nome}")
    print(f"Origem  : {origem}")
    print(f"Destino : s3://{BUCKET_NAME}/{destino}")

    if not os.path.exists(origem):
        print("ERRO: arquivo não encontrado localmente.")
        return False

    try:
        s3.upload_file(
            origem,
            BUCKET_NAME,
            destino
        )
        print("[OK] Upload realizado.")
        return True
    except ClientError as e:
        print("ERRO no upload:")
        print(e)
        return False


# ============================================================
# INGESTÃO
# ============================================================

def executar_ingestao():
    print()
    print("=" * 60)
    print("INICIANDO INGESTÃO")
    print("=" * 60)

    sucesso = 0
    erro = 0

    for nome, configuracao in ARQUIVOS.items():
        resultado = enviar_arquivo(
            nome,
            configuracao["origem"],
            configuracao["destino"]
        )

        if resultado:
            sucesso += 1
        else:
            erro += 1

    print()
    print("=" * 60)
    print("RESUMO DA INGESTÃO")
    print("=" * 60)
    print(f"Sucesso : {sucesso}")
    print(f"Erros   : {erro}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("       LAB 2 - INGESTÃO NO DATA LAKE")
    print("=" * 60)

    print(f"\nBucket: {BUCKET_NAME}")
    print(f"Data de ingestão: {DATA_INGESTAO}")

    # 1. Validar bucket
    if not testar_conexao():
        sys.exit(1)

    # 2. Executar ingestão
    executar_ingestao()

    print()
    print("=" * 60)
    print("INGESTÃO FINALIZADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
