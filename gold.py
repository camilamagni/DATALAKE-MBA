import boto3
import sys
import os
from datetime import datetime
import pandas as pd
from io import BytesIO, StringIO

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
    print("Uso: python gold.py NOME_DO_BUCKET")
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
# FUNÇÃO PARA LER PARQUET DO S3
# ============================================================

def ler_parquet_s3(chave):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=chave)
    return pd.read_parquet(BytesIO(obj["Body"].read()), engine="pyarrow")

# ============================================================
# PROCESSAMENTO GOLD
# ============================================================

def processar_gold():
    # Ler camada Silver
    silver_key = f"processed/fato_vendas/fato_vendas_{DATA_PROCESSAMENTO}.parquet"
    df = ler_parquet_s3(silver_key)

    # Agregações por UF e categoria
    gold_df = df.groupby(["estado", "categoria"]).agg(
        total_vendas=("valor_total", "sum"),
        quantidade_total=("quantidade", "sum"),
        ticket_medio=("valor_total", "mean")
    ).reset_index()

    # Persistir em Parquet/Snappy
    gold_parquet_key = f"gold/fato_vendas_agg/fato_vendas_gold_{DATA_PROCESSAMENTO}.parquet"
    buffer_parquet = BytesIO()
    gold_df.to_parquet(buffer_parquet, engine="pyarrow", compression="snappy", index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=gold_parquet_key, Body=buffer_parquet.getvalue())
    print(f"[OK] Camada Gold (Parquet) gravada em {gold_parquet_key}")

    # # Persistir também em CSV
    # gold_csv_key = f"gold/fato_vendas_agg/fato_vendas_gold_{DATA_PROCESSAMENTO}.csv"
    # buffer_csv = StringIO()
    # gold_df.to_csv(buffer_csv, index=False)
    # s3.put_object(Bucket=BUCKET_NAME, Key=gold_csv_key, Body=buffer_csv.getvalue(), ContentType="text/csv")
    # print(f"[OK] Camada Gold (CSV) gravada em {gold_csv_key}")

    # Mostrar primeiras linhas no terminal
    print("\nPré-visualização da Camada Gold:")
    print(gold_df.head())

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("PROCESSAMENTO CAMADA GOLD")
    print("=" * 60)
    processar_gold()
    print("=" * 60)
    print("CAMADA GOLD FINALIZADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
