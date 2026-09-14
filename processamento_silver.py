import boto3
import csv
import json
import sys
import os
from datetime import datetime
from io import StringIO
import pandas as pd  # Usaremos pandas para facilitar o join e salvar em Parquet

# ============================================================
# CARREGAR CREDENCIAIS
# ============================================================

def carregar_credenciais(caminhos_possiveis=["AWS_CREDENTIAL.env", "AWS_CREDENTIAL"]):
    credenciais = {}
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha and not linha.startswith("#") and "=" in linha:
                        chave, valor = linha.split("=", 1)
                        credenciais[chave.strip()] = valor.strip().strip('"').strip("'")
            break
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
    print("Uso: python processamento_silver.py NOME_DO_BUCKET")
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

DATA_PROCESSAMENTO = datetime.now().strftime("%Y-%m-%d")

# ============================================================
# FUNÇÃO PARA LER CSV DO S3 EM DATAFRAME
# ============================================================

def ler_csv_s3(chave):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=chave)
    conteudo = obj["Body"].read().decode("utf-8")
    return pd.read_csv(StringIO(conteudo))

# ============================================================
# PROCESSAMENTO
# ============================================================

def processar():
    # Carregar dimensões e fatos
    clientes = ler_csv_s3(f"raw/clientes/ingest_date={DATA_PROCESSAMENTO}/clientes.csv")
    produtos = ler_csv_s3(f"raw/produtos/ingest_date={DATA_PROCESSAMENTO}/produtos.csv")
    pedidos = ler_csv_s3(f"raw/pedidos/ingest_date={DATA_PROCESSAMENTO}/pedidos.csv")

    # Regras de qualidade
    rejeitados = []
    pedidos_validos = []

    for _, pedido in pedidos.iterrows():
        motivo = None

        if int(pedido["quantidade"]) <= 0:
            motivo = "Quantidade inválida"
        elif str(pedido["cliente_id"]) not in clientes["cliente_id"].astype(str).values:
            motivo = "Cliente inexistente"
        elif str(pedido["produto_id"]) not in produtos["produto_id"].astype(str).values:
            motivo = "Produto inexistente"

        if motivo:
            rejeitados.append({"pedido_id": pedido["pedido_id"], "motivo": motivo, "registro": pedido.to_dict()})
        else:
            pedidos_validos.append(pedido.to_dict())

    # Gravar rejeitados em JSON
    rejeitados_key = f"quarantine/pedidos_rejeitados/data={DATA_PROCESSAMENTO}/rejeitados.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=rejeitados_key,
        Body="\n".join(json.dumps(r, ensure_ascii=False) for r in rejeitados),
        ContentType="application/json"
    )
    print(f"[OK] Rejeitados gravados em {rejeitados_key}")

    # Converter válidos em DataFrame
    pedidos_validos_df = pd.DataFrame(pedidos_validos)

    # JOIN com clientes e produtos
    silver_df = pedidos_validos_df.merge(clientes, on="cliente_id", how="left") \
                                  .merge(produtos, on="produto_id", how="left")

    # Calcular valor_total
    silver_df["valor_total"] = silver_df["quantidade"].astype(float) * silver_df["preco"].astype(float)

    # Persistir em Parquet/Snappy
    silver_key = f"processed/fato_vendas/fato_vendas_{DATA_PROCESSAMENTO}.parquet"
    buffer = StringIO()
    silver_df.to_parquet("fato_vendas.parquet", engine="pyarrow", compression="snappy", index=False)

    # Mostrar primeiras linhas no terminal
    print("\nPré-visualização da Camada Silver:")
    print(silver_df.head())
    print(silver_df.columns)
    print(len(pedidos_validos))
    print(len(rejeitados))
    print(len(silver_df))

    # Upload para S3
    with open("fato_vendas.parquet", "rb") as data:
        s3.put_object(Bucket=BUCKET_NAME, Key=silver_key, Body=data)

    print(f"[OK] Silver gravado em {silver_key}")

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("PROCESSAMENTO DE DATA QUALITY E SILVER")
    print("=" * 60)
    processar()
    print("=" * 60)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 60)

if __name__ == "__main__":
    main()
