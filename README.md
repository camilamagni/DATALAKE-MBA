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

xxxxxxxxxx imagem das pastas da AWS xxxxxxxxxxxxxxxx

4. **Gerar dados**
     * Executar script **“gerar_dados.py”** dentro da subpasta Dados --- python gerar_dados.py [Número de linhas]
     * O que faz: gera dados fictícios de clientes, produtos e pedidos em CSV, incluindo anomalias (quantidades negativas, IDs de produtos inválidos).
  
5. **Ingestão e Particionamento S3 (Raw Layer)**
     * Executar script **“ingestao.py”** --- python ingestao.py [Nome do Bucket]
     * O que faz: carrega os arquivos CSV para o bucket S3, organizando-os na camada raw em estrutura de diretórios particionada por data de ingestão (Hive Style):
s3://<seu-bucket>/raw/clientes/ingest_date=YYYY-MM-DD/clientes.csv
  
6. **Data Quality, Quarentena e Processamento (Silver Layer)**
     * Executar script **“processamento_silver.py”** --- python processamento_silver.py [Nome do Bucket]
     * O que faz: Aplica regras de qualidade, rejeitando pedidos inválidos (pedido_id fora do intevalo válido de 9001 a 10000, quantidades negativas); 
Grava rejeitados em quarantine/ (JSON);
Enriquecer pedidos válidos com dados de clientes e produtos;
Calcula valor_total;
Salva em processed/ (Parquet).

7. **Agregações (Gold Layer)**
     * Executar script **“gold.py”** --- python gold.py [Nome do Bucket]
     * O que faz: gera agregações de vendas por estado e categoria, calculando métricas como total de vendas, quantidade total e ticket médio.

8. **Auditoria e Validação Athena**
     * Executar script “setup_athena.py” --- python setup_athena.py [Nome do Bucket]
     * O que faz: cria tabelas externas no Athena para Raw, Quarentena, Silver e Gold; repara partições; executa queries de validação (metadados e conciliação de integridade).
