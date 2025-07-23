import os
import sqlite3
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
DB_PATH = os.path.join(DATA_DIR, 'ecom_data.db')

# Map CSV filenames to simple table names
CSV_TO_TABLE = {
    'eligibility.csv': 'eligibility',
    'sales.csv': 'sales',
    'total_sales.csv': 'total_sales',
}

def load_csv_to_sqlite(csv_path, table_name, conn):
    print(f'Loading {csv_path} into table {table_name}...')
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f'Loaded {len(df)} rows into {table_name}')

def main():
    conn = sqlite3.connect(DB_PATH)
    for csv_file, table_name in CSV_TO_TABLE.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        load_csv_to_sqlite(csv_path, table_name, conn)
    conn.close()
    print('All CSV files loaded successfully.')

if __name__ == '__main__':
    main() 