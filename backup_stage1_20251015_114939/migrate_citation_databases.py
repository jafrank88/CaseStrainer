#!/usr/bin/env python3
"""
Migrate and merge all citation and parallel citation data from data/citations.db into src/citations.db.
Ensures all relevant columns exist and updates/inserts as needed.
Does NOT change any verification logic.
"""

import sqlite3
import os

SRC_DB = os.path.join('src', 'citations.db')
DATA_DB = os.path.join('data', 'citations.db')

CITATION_COLUMNS = [
    'citation_text', 'case_name', 'confidence', 'found', 'explanation', 'source', 'source_document',
    'url', 'context', 'date_added', 'file_link', 'parties', 'year', 'court', 'volume', 'reporter', 'page', 'date_filed', 'docket_number'
]

PARALLEL_COLUMNS = [
    'citation_id', 'citation', 'reporter', 'category', 'year', 'date_added'
]

def ensure_columns(conn, table, columns):
    """Ensure all columns exist in the given table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for col in columns:
        if col not in existing:
            # Default to TEXT if not known
            col_type = 'TEXT'
            if col in ('confidence',):
                col_type = 'REAL'
            elif col in ('found',):
                col_type = 'BOOLEAN'
            elif col in ('citation_id',):
                col_type = 'INTEGER'
            elif col in ('date_added', 'date_filed'):
                col_type = 'TIMESTAMP'
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                print(f"Added column {col} to {table}")
            except Exception as e:
                print(f"Warning: Could not add column {col} to {table}: {e}")
    conn.commit()

def get_rows(conn, table, columns):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    result = []
    for row in rows:
        row_dict = dict(zip(col_names, row))
        # Only keep relevant columns
        filtered = {col: row_dict.get(col) for col in columns if col in row_dict}
        result.append(filtered)
    return result

def get_citation_id(conn, citation_text):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM citations WHERE citation_text = ?", (citation_text,))
    row = cursor.fetchone()
    return row[0] if row else None

def upsert_citation(conn, citation):
    cursor = conn.cursor()
    # Try to update first
    set_clause = ', '.join([f"{col} = ?" for col in citation if col != 'citation_text'])
    values = [citation[col] for col in citation if col != 'citation_text'] + [citation['citation_text']]
    cursor.execute(f"UPDATE citations SET {set_clause} WHERE citation_text = ?", values)
    if cursor.rowcount == 0:
        # Insert if not exists
        cols = ', '.join(citation.keys())
        placeholders = ', '.join(['?'] * len(citation))
        cursor.execute(f"INSERT INTO citations ({cols}) VALUES ({placeholders})", [citation[col] for col in citation])
    conn.commit()

def upsert_parallel_citation(conn, parallel, citation_id):
    cursor = conn.cursor()
    # Try to update first
    set_clause = ', '.join([f"{col} = ?" for col in parallel if col != 'citation'])
    values = [parallel[col] for col in parallel if col != 'citation'] + [citation_id, parallel['citation']]
    cursor.execute(f"UPDATE parallel_citations SET {set_clause} WHERE citation_id = ? AND citation = ?", values)
    if cursor.rowcount == 0:
        # Insert if not exists
        cols = ', '.join(['citation_id'] + list(parallel.keys()))
        placeholders = ', '.join(['?'] * (1 + len(parallel)))
        cursor.execute(f"INSERT INTO parallel_citations ({cols}) VALUES ({placeholders})", [citation_id] + [parallel[col] for col in parallel])
    conn.commit()

def main():
    if not os.path.exists(DATA_DB):
        print(f"Source database not found: {DATA_DB}")
        return
    if not os.path.exists(SRC_DB):
        print(f"Target database not found: {SRC_DB}")
        return
    src_conn = sqlite3.connect(SRC_DB)
    data_conn = sqlite3.connect(DATA_DB)
    # Ensure all columns exist
    ensure_columns(src_conn, 'citations', CITATION_COLUMNS)
    ensure_columns(src_conn, 'parallel_citations', PARALLEL_COLUMNS)
    ensure_columns(data_conn, 'citations', CITATION_COLUMNS)
    # Migrate citations
    data_citations = get_rows(data_conn, 'citations', CITATION_COLUMNS)
    print(f"Found {len(data_citations)} citations in data/citations.db")
    for citation in data_citations:
        if not citation.get('citation_text'):
            continue
        upsert_citation(src_conn, citation)
    # Migrate parallel citations if table exists
    try:
        data_conn.execute("SELECT 1 FROM parallel_citations LIMIT 1")
        data_parallels = get_rows(data_conn, 'parallel_citations', PARALLEL_COLUMNS)
        print(f"Found {len(data_parallels)} parallel citations in data/citations.db")
        for parallel in data_parallels:
            if not parallel.get('citation'):
                continue
            # Find the citation_id in the target DB
            citation_id = parallel.get('citation_id')
            if not citation_id and 'citation_text' in parallel:
                citation_id = get_citation_id(src_conn, parallel['citation_text'])
            # If citation_id is not found, try to match by citation text
            if not citation_id:
                continue
            upsert_parallel_citation(src_conn, parallel, citation_id)
    except Exception as e:
        print(f"No parallel_citations table or error: {e}")
    src_conn.close()
    data_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    main() 