# Importação de bibliotecas
import os # Operações com diretórios e caminhos de arquivos
import pandas as pd # Manipulação de DataFrames e leitura de arquivos CSV
from sqlalchemy import create_engine, text
# Definição das variáveis de ambiente e credenciais de acesso ao PostgreSQL no Docker
DB_USER = "postgres"
DB_PASS = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "iot_db"
# Montagem da URL de conexão estruturada para o SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)


def drop_table_cascade(connection):
    print("A limpar tabela antiga e objetos dependentes...")
    connection.execute(
        text("DROP TABLE IF EXISTS temperature_readings CASCADE;")
    )
    connection.commit()

# Função responsável pela criação das Views SQL no PostgreSQL
def create_views(connection):
    print("A criar Views SQL atualizadas...")
    views_script = """
    -- View 1: Média de temperatura por localização (In vs Out)
    CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
    SELECT 
        "out/in" AS device_id, 
        ROUND(AVG(temperature)::numeric, 2) AS avg_temp
    FROM temperature_readings
    WHERE temperature IS NOT NULL
    GROUP BY "out/in";

    -- View 2: Contagem de leituras por hora do dia
    CREATE OR REPLACE VIEW leituras_por_hora AS
    SELECT 
        EXTRACT(HOUR FROM noted_date) AS hora,
        COUNT(*) AS contagem
    FROM temperature_readings
    WHERE noted_date IS NOT NULL
    GROUP BY hora
    ORDER BY hora;

    -- View 3: Temperaturas máximas e mínimas por dia
    CREATE OR REPLACE VIEW temp_max_min_por_dia AS
    SELECT 
        DATE(noted_date) AS data,
        MAX(temperature) AS temp_max,
        MIN(temperature) AS temp_min
    FROM temperature_readings
    WHERE noted_date IS NOT NULL
    GROUP BY DATE(noted_date)
    ORDER BY data;
    """
    connection.execute(text(views_script))
    connection.commit()
    print("Views SQL criadas com sucesso!")


def process_and_ingest():
    csv_path = os.path.join("data", "IoT-temp.csv") # Define o caminho até o arquivo CSV contendo as leituras dos sensores

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Ficheiro não encontrado em: {csv_path}")

    print("A carregar ficheiro CSV...")
    df = pd.read_csv(csv_path)

    # Padroniza apenas os nomes das colunas
    df.columns = df.columns.str.strip().str.lower()

    if "temp" in df.columns:
        df = df.rename(columns={"temp": "temperature"})

    print("A ajustar formato das datas...")
    df["noted_date"] = pd.to_datetime(
        df["noted_date"], format="mixed", errors="coerce"
    )

    with engine.connect() as connection:
        drop_table_cascade(connection)

    print("A enviar dados para o PostgreSQL...")
    df.to_sql(
        name="temperature_readings",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )

    with engine.connect() as connection:
        create_views(connection)

    print("Pipeline de ingestão concluído com sucesso!")


if __name__ == "__main__":
    process_and_ingest()