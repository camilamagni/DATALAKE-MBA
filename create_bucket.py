import boto3
import sys
import os
import re

from botocore.exceptions import ClientError
from datetime import datetime


# ============================================================
# CARREGAR CREDENCIAIS DO ARQUIVO
# ============================================================

def carregar_credenciais(caminho_arquivo="AWS_CREDENTIAL"):
    if not os.path.exists(caminho_arquivo):
        print(f"\nERRO: Arquivo de credenciais '{caminho_arquivo}' não encontrado.")
        sys.exit(1)

    credenciais = {}
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                credenciais[chave.strip()] = valor.strip().strip('"').strip("'")

    chaves_obrigatorias = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for chave in chaves_obrigatorias:
        if chave not in credenciais:
            print(f"\nERRO: Chave '{chave}' ausente no arquivo '{caminho_arquivo}'.")
            sys.exit(1)

    return credenciais


CREDS = carregar_credenciais("AWS_CREDENTIAL")

AWS_ACCESS_KEY_ID = CREDS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = CREDS["AWS_SECRET_ACCESS_KEY"]
AWS_SESSION_TOKEN = CREDS.get("AWS_SESSION_TOKEN")
AWS_REGION = CREDS["AWS_REGION"]


# ============================================================
# VERIFICAR ARGUMENTOS
# ============================================================

if len(sys.argv) != 2:
    print()
    print("Uso:")
    print("    python create_bucket.py NOME_DO_BUCKET")
    print()
    print("Exemplo:")
    print("    python create_bucket.py datalake-turma-01-aluno-9999")
    print()
    sys.exit(1)


BUCKET_NAME = sys.argv[1]


# ============================================================
# VALIDAR NOME DO BUCKET
# ============================================================

def validar_nome_bucket(nome):
    if len(nome) < 3 or len(nome) > 63:
        return False, "O nome deve possuir entre 3 e 63 caracteres."

    if not re.match(r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$", nome):
        return False, (
            "Use apenas letras minúsculas, números, "
            "ponto (.) e hífen (-)."
        )

    if ".." in nome:
        return False, "O nome não pode conter dois pontos consecutivos."

    if re.match(r"^\d+\.\d+\.\d+\.\d+$", nome):
        return False, "O nome não pode ter formato de endereço IP."

    if nome.startswith("xn--"):
        return False, "O nome não pode começar com 'xn--'."

    if nome.startswith("sthree-"):
        return False, "O nome não pode começar com 'sthree-'."

    if nome.startswith("amzn-s3-demo-"):
        return False, "Prefixo reservado pela AWS."

    if nome.endswith("-s3alias"):
        return False, "Sufixo reservado pela AWS."

    return True, ""


valido, mensagem = validar_nome_bucket(BUCKET_NAME)

if not valido:
    print()
    print("ERRO: NOME DE BUCKET INVÁLIDO")
    print("-" * 60)
    print(mensagem)
    print()
    sys.exit(1)


# ============================================================
# CLIENTE S3
# ============================================================

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)


# ============================================================
# TESTAR CONEXÃO
# ============================================================

def testar_conexao():
    print("\nTestando conexão com AWS...")
    try:
        s3.list_buckets()
        print("Conexão realizada com sucesso!")
        return True
    except ClientError as e:
        print("\nErro ao conectar com AWS:")
        print(e)
        return False


# ============================================================
# CRIAR BUCKET
# ============================================================

def criar_bucket():
    print()
    print(f"Bucket informado : {BUCKET_NAME}")
    print(f"Região           : {AWS_REGION}")
    print()

    try:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": AWS_REGION
            }
        )
        print("Bucket criado com sucesso!")
        return True

    except ClientError as e:
        codigo = e.response["Error"]["Code"]

        print()
        print("ERRO AO CRIAR BUCKET")
        print("-" * 60)
        print(f"Código AWS : {codigo}")
        print(f"Mensagem   : {e}")
        print()

        if codigo == "BucketAlreadyOwnedByYou":
            print("O bucket já existe e pertence à sua conta.")
            return True

        if codigo == "BucketAlreadyExists":
            print("O nome já está sendo utilizado por outra conta AWS.")
            return False

        return False


# ============================================================
# CRIAR ESTRUTURA DO DATA LAKE
# ============================================================

def criar_estrutura():
    data = datetime.now().strftime("%Y-%m-%d")

    estrutura = [
        "raw/",
        "raw/pedidos/",
        "raw/clientes/",
        "raw/produtos/",
        "quarantine/",
        "quarantine/pedidos_rejeitados/",
        ### f"quarantine/pedidos_rejeitados/data={data}/",
        "processed/",
        "processed/fato_vendas/",
        "gold/",
        "athena_results"
    ]

    print()
    print("Criando estrutura do Data Lake...")
    print()

    try:
        for pasta in estrutura:
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=pasta
            )
            print(f"[OK] {pasta}")
        return True

    except ClientError as e:
        print()
        print("ERRO AO CRIAR ESTRUTURA")
        print("-" * 60)
        print(e)
        return False


# ============================================================
# LISTAR ESTRUTURA
# ============================================================

def listar_estrutura():
    print()
    print("=" * 60)
    print("ESTRUTURA DO DATA LAKE")
    print("=" * 60)

    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME
        )

        if "Contents" not in response:
            print("Bucket vazio.")
            return

        for objeto in response["Contents"]:
            print(objeto["Key"])

    except ClientError as e:
        print("Erro ao listar bucket:")
        print(e)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("       LAB - DATA LAKE NO AMAZON S3")
    print("=" * 60)

    print(f"\nBucket: {BUCKET_NAME}")

    if not testar_conexao():
        sys.exit(1)

    if not criar_bucket():
        print()
        print("O bucket não foi criado.")
        print("O programa será encerrado.")
        print()
        sys.exit(1)

    if not criar_estrutura():
        print()
        print("Não foi possível criar a estrutura.")
        sys.exit(1)

    listar_estrutura()

    print()
    print("=" * 60)
    print("DATA LAKE CRIADO COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    main()