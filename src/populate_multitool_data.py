import sqlite3

# Sample citation data
sample_citations = [
    {
        "citation_text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "brief_url": "https://example.com/brief1",
        "context": "The landmark case Brown v. Board of Education established that separate educational facilities are inherently unequal.",
        "verification_source": "Justia",
        "verification_confidence": 0.95,
        "verification_explanation": "Citation found on Justia with full text of the opinion available.",
    },
    {
        "citation_text": "Roe v. Wade, 410 U.S. 113 (1973)",
        "brief_url": "https://example.com/brief2",
        "context": "The Court's decision in Roe v. Wade recognized a woman's right to choose an abortion.",
        "verification_source": "FindLaw",
        "verification_confidence": 0.92,
        "verification_explanation": "Citation found on FindLaw with complete case details.",
    },
    {
        "citation_text": "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "brief_url": "https://example.com/brief3",
        "context": "Miranda v. Arizona established the requirement for police to inform suspects of their rights.",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.90,
        "verification_explanation": "Citation found on Google Scholar with full text and citations.",
    },
    {
        "citation_text": "Obergefell v. Hodges, 576 U.S. 644 (2015)",
        "brief_url": "https://example.com/brief4",
        "context": "Obergefell v. Hodges guaranteed the fundamental right to marry to same-sex couples.",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.88,
        "verification_explanation": "Citation found on Leagle.com with complete case details.",
    },
    {
        "citation_text": "Citizens United v. FEC, 558 U.S. 310 (2010)",
        "brief_url": "https://example.com/brief5",
        "context": "Citizens United v. FEC struck down restrictions on independent expenditures by corporations.",
        "verification_source": "Justia",
        "verification_confidence": 0.85,
        "verification_explanation": "Citation found on Justia with full opinion text.",
    },
]


def create_table_if_not_exists(conn):
    """Create the multitool_confirmed_citations table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS multitool_confirmed_citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        brief_url TEXT,
        context TEXT,
        verification_source TEXT,
        verification_confidence REAL,
        verification_explanation TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()


def populate_sample_data(conn):
    """Populate the table with sample citation data."""
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM multitool_confirmed_citations")

    # Insert sample data
    for citation in sample_citations:
        cursor.execute(
            """
        INSERT INTO multitool_confirmed_citations 
        (citation_text, brief_url, context, verification_source, verification_confidence, verification_explanation)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                citation["citation_text"],
                citation["brief_url"],
                citation["context"],
                citation["verification_source"],
                citation["verification_confidence"],
                citation["verification_explanation"],
            ),
        )

    conn.commit()
    print(
        f"Added {len(sample_citations)} sample citations to the multitool_confirmed_citations table."
    )


def main():
    """Main function to create and populate the multitool_confirmed_citations table."""
    try:
        # Connect to the database
        conn = sqlite3.connect("citations.db")

        # Create table if it doesn't exist
        create_table_if_not_exists(conn)

        # Populate with sample data
        populate_sample_data(conn)

        # Verify the data was added
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM multitool_confirmed_citations")
        count = cursor.fetchone()[0]
        print(f"Total records in multitool_confirmed_citations: {count}")

        # Close the connection
        conn.close()

        print("Sample data successfully added to the database.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
