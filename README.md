# DATALAKE-MBA
Repositório destinado às atividades da disciplina **Data Lakes, Lakehouses e Data Meshes** do MBA em Inteligência de Dados.

## ATIVIDADE: Data Lake Pipeline

Este projeto implementa um pipeline completo de **Data Lake na AWS** utilizando **S3, Python, Pandas, PyArrow e Athena**. O fluxo cobre desde a geração e ingestão de dados brutos (Raw Layer), passando pela aplicação de regras de qualidade e enriquecimento (Silver Layer), até a criação de agregações de negócio (Gold Layer). Por fim, o ambiente é preparado no Athena com tabelas externas e queries de validação, permitindo auditoria de integridade e consultas analíticas sobre os dados processados.

### Guia de Execução do Pipeline

1. **Configurar credenciais**
     * Preencher credenciais no arquivo **“AWS Credentials”**
2. **Instalar dependências**
     * Instalar as bibliotecas necessárias (boto3, pandas e pyarrow) via pip install.
3. **Criar Bucket no Amazon S3**
     * Executar script **“create bucket.py”** --- python create_bucket.py [Nome do Bucket]
     * O que faz: cria o bucket no S3 que será usado como Data Lake e a estrutura de pastas (raw/, quarantine/, processed/, gold/ e athena-results/).
     * Estrutura de pastas criada no S3:

<img width="638" height="352" alt="image" src="https://github.com/user-attachments/assets/f9732bc7-f4a2-4d9c-bb1f-5b3ccd68f8c6" />
<img width="620" height="495" alt="image" src="https://github.com/user-attachments/assets/4f9f4659-6f37-4219-8bcd-d3740d6422e7" />

4. **Gerar dados**
     * Executar script **“gerar_bases.py”** dentro da subpasta Dados --- python gerar_bases.py [Número de linhas]
     * O que faz: gera dados fictícios de clientes, produtos e pedidos em CSV, incluindo anomalias (quantidades negativas, IDs de produtos inválidos).

<img width="484" height="269" alt="image" src="https://github.com/user-attachments/assets/f628383c-5fcd-4bf1-a46a-fc6227ef8126" />
<img width="698" height="307" alt="image" src="https://github.com/user-attachments/assets/c739fec3-44a4-4db1-a6e3-c2df21ed0eee" />

5. **Ingestão e Particionamento S3 (Raw Layer)**
     * Executar script **“ingestao.py”** --- python ingestao.py [Nome do Bucket]
     * O que faz: carrega os arquivos CSV para o bucket S3, organizando-os na camada raw em estrutura de diretórios particionada por data de ingestão (Hive Style):
s3://<seu-bucket>/raw/clientes/ingest_date=YYYY-MM-DD/clientes.csv

<img width="546" height="185" alt="image" src="https://github.com/user-attachments/assets/9c7e357e-fea1-4a34-978b-3a4a629f2f83" />

6. **Data Quality, Quarentena e Processamento (Silver Layer)**
     * Executar script **“processamento_silver.py”** --- python processamento_silver.py [Nome do Bucket]
     * O que faz: Aplica regras de qualidade, rejeitando pedidos inválidos (pedido_id fora do intevalo válido de 9001 a 10000, quantidades negativas); 
Grava rejeitados em quarantine/ (JSON);
Enriquecer pedidos válidos com dados de clientes e produtos;
Calcula valor_total;
Salva em processed/ (Parquet).

<img width="495" height="122" alt="image" src="https://github.com/user-attachments/assets/aad85b5b-2b07-4853-9b8c-462c65b6d822" />
<img width="403" height="197" alt="image" src="https://github.com/user-attachments/assets/98bb8497-306e-4cc9-9454-f998374ee7ab" />
<img width="431" height="193" alt="image" src="https://github.com/user-attachments/assets/5f699b14-69d1-4685-abc0-a3d46da9135e" />

7. **Agregações (Gold Layer)**
     * Executar script **“gold.py”** --- python gold.py [Nome do Bucket]
     * O que faz: gera agregações de vendas por estado e categoria, calculando métricas como total de vendas, quantidade total e ticket médio.
  
<img width="424" height="115" alt="image" src="https://github.com/user-attachments/assets/5bdb19ef-7d61-42d7-bf64-7367d1bb98a4" />
<img width="401" height="205" alt="image" src="https://github.com/user-attachments/assets/ab3e94fb-dabb-48a3-a20e-727c23bf2603" />

8. **Auditoria e Validação Athena**
     * Executar script “setup_athena.py” --- python setup_athena.py [Nome do Bucket]
     * O que faz: cria tabelas externas no Athena para Raw, Quarentena, Silver e Gold; repara partições; executa queries de validação (metadados e conciliação de integridade).
  
<img width="823" height="389" alt="image" src="https://github.com/user-attachments/assets/31d38391-1ca7-4ca6-887a-2f280bc8d17e" />
<img width="823" height="392" alt="image" src="https://github.com/user-attachments/assets/5e6c594a-85c9-433d-80ce-46685e39d947" />

Primeira Query:

    SELECT "$path", "$file_size" FROM raw_pedidos LIMIT 10;
    
Segunda Query:

    WITH raw_count AS (
            SELECT COUNT(*) AS total_raw FROM raw_pedidos), 
        silver_count AS (
            SELECT COUNT(*) AS total_silver FROM silver_fato_vendas),
        quarentena_count AS (
            SELECT COUNT(*) AS total_quarentena FROM quarentena_pedidos)
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
