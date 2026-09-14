import boto3
import sys
import os
import time
import re
from botocore.exceptions import ClientError

# ============================================================
# CARREGAR CREDENCIAIS
# ============================================================

def carregar_credenciais(caminhos_possiveis=["AWS_CREDENTIAL.env", "AWS_CREDENTIAL"]):
    caminho_encontrado = None
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            caminho_encontrado = caminho
            break
    if not caminho_encontrado:
        print(f"\nERRO: Nenhum arquivo de credenciais encontrado.")
        sys.exit(1)

    credenciais = {}
    with open(caminho_encontrado, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                credenciais[chave.strip()] = valor.strip().strip('"').strip("'")
    return credenciais

# ============================================================
# ARGUMENTO E CONFIGURAÇÃO
# ============================================================

if len(sys.argv) != 2:
    print("Uso: python setup_athena.py NOME_DO_BUCKET")
    sys.exit(1)

BUCKET_NAME = sys.argv[1]
CREDS = carregar_credenciais()

AWS_ACCESS_KEY_ID = CREDS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = CREDS["AWS_SECRET_ACCESS_KEY"]
AWS_SESSION_TOKEN = CREDS.get("AWS_SESSION_TOKEN")
AWS_REGION = CREDS["AWS_REGION"]

DB_SUFFIX = re.sub(r"[^a-zA-Z0-9_]", "_", BUCKET_NAME).lower()
DATABASE_NAME = f"datalake_db_{DB_SUFFIX}"
OUTPUT_LOCATION = f"s3://{BUCKET_NAME}/athena-results/"

# ============================================================
# CLIENTE ATHENA
# ============================================================

athena = boto3.client(
    "athena",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

# ============================================================
# EXECUTOR DE QUERIES
# ============================================================

def executar_query(query, database=None, descricao="Executando comando"):
    print(f"\n-> {descricao}...")
    params = {
        "QueryString": query,
        "ResultConfiguration": {"OutputLocation": OUTPUT_LOCATION}
    }
    if database:
        params["QueryExecutionContext"] = {"Database": database}

    response = athena.start_query_execution(**params)
    qid = response["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]["State"]
        if status == "SUCCEEDED":
            print(f"[OK] Sucesso ({qid})")
            return qid
        elif status in ["FAILED", "CANCELLED"]:
            print(f"[ERRO] Falha na query ({status})")
            return None
        time.sleep(1)

# ============================================================
# DDL SETUP
# ============================================================

QUERIES_SETUP = [
    ("Criando Banco de Dados", None, f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME};"),

    # DROP antigas
    ("Drop raw_clientes", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.raw_clientes;"),
    ("Drop raw_produtos", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.raw_produtos;"),
    ("Drop raw_pedidos", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.raw_pedidos;"),
    ("Drop quarentena_pedidos", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.quarentena_pedidos;"),
    ("Drop silver_fato_vendas", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.silver_fato_vendas;"),
    ("Drop gold_vendas_uf_categoria", DATABASE_NAME, f"DROP TABLE IF EXISTS {DATABASE_NAME}.gold_vendas_uf_categoria;"),

    # RAW CLIENTES
    ("Criando raw_clientes", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.raw_clientes (
            cliente_id INT,
            nome STRING,
            cidade STRING,
            estado STRING
        )
        PARTITIONED BY (ingest_date STRING)
        ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{BUCKET_NAME}/raw/clientes/'
        TBLPROPERTIES ('skip.header.line.count'='1');
    """),

    # RAW PRODUTOS
    ("Criando raw_produtos", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.raw_produtos (
            produto_id INT,
            nome STRING,
            categoria STRING,
            preco DOUBLE
        )
        PARTITIONED BY (ingest_date STRING)
        ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{BUCKET_NAME}/raw/produtos/'
        TBLPROPERTIES ('skip.header.line.count'='1');
    """),

    # RAW PEDIDOS
    ("Criando raw_pedidos", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.raw_pedidos (
            pedido_id INT,
            cliente_id INT,
            produto_id INT,
            quantidade INT,
            valor DOUBLE,
            data_pedido STRING
        )
        PARTITIONED BY (ingest_date STRING)
        ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{BUCKET_NAME}/raw/pedidos/'
        TBLPROPERTIES ('skip.header.line.count'='1');
    """),

    # QUARENTENA
    ("Criando quarentena_pedidos", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.quarentena_pedidos (
            pedido_id INT,
            motivo STRING,
            registro MAP<STRING,STRING>
        )
        PARTITIONED BY (data STRING)
        ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
        STORED AS TEXTFILE
        LOCATION 's3://{BUCKET_NAME}/quarantine/pedidos_rejeitados/';
    """),

    # SILVER
    ("Criando silver_fato_vendas", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.silver_fato_vendas (
            pedido_id INT,
            cliente_id INT,
            produto_id INT,
            quantidade INT,
            valor_total DOUBLE,
            data_pedido STRING,
            categoria STRING,
            nome_produto STRING,
            nome STRING,
            cidade STRING,
            estado STRING
        )
        STORED AS PARQUET
        LOCATION 's3://{BUCKET_NAME}/processed/fato_vendas/';
    """),

    # GOLD
    ("Criando gold_vendas_uf_categoria", DATABASE_NAME, f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.gold_vendas_uf_categoria (
            estado STRING,
            categoria STRING,
            total_vendas DOUBLE,
            quantidade_total INT,
            ticket_medio DOUBLE
        )
        STORED AS PARQUET
        LOCATION 's3://{BUCKET_NAME}/gold/fato_vendas_agg/';
    """),

    # Reparar partições
    ("Reparando raw_clientes", DATABASE_NAME, f"MSCK REPAIR TABLE {DATABASE_NAME}.raw_clientes;"),
    ("Reparando raw_produtos", DATABASE_NAME, f"MSCK REPAIR TABLE {DATABASE_NAME}.raw_produtos;"),
    ("Reparando raw_pedidos", DATABASE_NAME, f"MSCK REPAIR TABLE {DATABASE_NAME}.raw_pedidos;"),
    ("Reparando quarentena_pedidos", DATABASE_NAME, f"MSCK REPAIR TABLE {DATABASE_NAME}.quarentena_pedidos;")
]

# ============================================================
# TESTES ANALÍTICOS
# ============================================================

def testar_consultas():
    # Metadados
    query_meta = f'SELECT "$path", "$file_size" FROM {DATABASE_NAME}.raw_pedidos LIMIT 10;'
    qid_meta = executar_query(query_meta, DATABASE_NAME, "Consulta de Metadados (raw_pedidos)")
    if qid_meta:
        resultados = athena.get_query_results(QueryExecutionId=qid_meta)
        print("\n--- Resultado Metadados ---")
        for linha in resultados["ResultSet"]["Rows"]:
            valores = [col.get("VarCharValue", "") for col in linha["Data"]]
            print(" | ".join(valores))

    # Conciliação de integridade
    query_conc = f"""
    WITH raw_count AS (
        SELECT COUNT(*) AS total_raw FROM {DATABASE_NAME}.raw_pedidos
    ),
    silver_count AS (
        SELECT COUNT(*) AS total_silver FROM {DATABASE_NAME}.silver_fato_vendas
    ),
    quarentena_count AS (
        SELECT COUNT(*) AS total_quarentena FROM {DATABASE_NAME}.quarentena_pedidos
    )
    SELECT 
        r.total_raw,
        s.total_silver,
        q.total_quarentena,
        CASE 
            WHEN r.total_raw = (s.total_silver + q.total_quarentena) 
            THEN 'OK' 
            ELSE 'DIVERGENTE' 
        END AS resultado
    FROM raw_count r
    CROSS JOIN silver_count s
    CROSS JOIN quarentena_count q;
    """
    qid_conc = executar_query(query_conc, DATABASE_NAME, "Conciliação de Integridade")
    if qid_conc:
        resultados = athena.get_query_results(QueryExecutionId=qid_conc)
        print("\n--- Resultado Conciliação ---")
        for linha in resultados["ResultSet"]["Rows"]:
            valores = [col.get("VarCharValue", "") for col in linha["Data"]]
            print(" | ".join(valores))

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("      SETUP DO AMAZON ATHENA / DATA CATALOG")
    print("=" * 60)
    print(f"Bucket Alvo     : {BUCKET_NAME}")
    print(f"Database Gerado : {DATABASE_NAME}")
    print(f"Output Queries  : {OUTPUT_LOCATION}")

    # Executar todas as queries de setup
    for descricao, db, sql in QUERIES_SETUP:
        res = executar_query(sql, db, descricao)
        if not res:
            print("\nInterrompendo devido a erro no setup.")
            sys.exit(1)

    print("\nEstrutura de tabelas sincronizada com sucesso!")

    # Executar testes analíticos
    testar_consultas()

    print("\nSetup e validações concluídos com sucesso!")
    print("=" * 60)

if __name__ == "__main__":
    main()