import sqlite3
import logging
from .config import get_database_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample citation data for 33 citations
sample_citations = [
    {
        "citation_text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "verification_source": "Justia",
        "verification_confidence": 0.95,
    },
    {
        "citation_text": "Roe v. Wade, 410 U.S. 113 (1973)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.92,
    },
    {
        "citation_text": "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.90,
    },
    {
        "citation_text": "Obergefell v. Hodges, 576 U.S. 644 (2015)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.88,
    },
    {
        "citation_text": "Citizens United v. FEC, 558 U.S. 310 (2010)",
        "verification_source": "Justia",
        "verification_confidence": 0.85,
    },
    {
        "citation_text": "Marbury v. Madison, 5 U.S. 137 (1803)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.94,
    },
    {
        "citation_text": "Gideon v. Wainwright, 372 U.S. 335 (1963)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.91,
    },
    {
        "citation_text": "Mapp v. Ohio, 367 U.S. 643 (1961)",
        "verification_source": "Justia",
        "verification_confidence": 0.89,
    },
    {
        "citation_text": "New York Times Co. v. Sullivan, 376 U.S. 254 (1964)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.87,
    },
    {
        "citation_text": "Loving v. Virginia, 388 U.S. 1 (1967)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.93,
    },
    {
        "citation_text": "District of Columbia v. Heller, 554 U.S. 570 (2008)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.86,
    },
    {
        "citation_text": "Tinker v. Des Moines, 393 U.S. 503 (1969)",
        "verification_source": "Justia",
        "verification_confidence": 0.84,
    },
    {
        "citation_text": "United States v. Nixon, 418 U.S. 683 (1974)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.82,
    },
    {
        "citation_text": "Bush v. Gore, 531 U.S. 98 (2000)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.80,
    },
    {
        "citation_text": "Plessy v. Ferguson, 163 U.S. 537 (1896)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.92,
    },
    {
        "citation_text": "Dred Scott v. Sandford, 60 U.S. 393 (1857)",
        "verification_source": "Justia",
        "verification_confidence": 0.91,
    },
    {
        "citation_text": "Korematsu v. United States, 323 U.S. 214 (1944)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.89,
    },
    {
        "citation_text": "Lochner v. New York, 198 U.S. 45 (1905)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.88,
    },
    {
        "citation_text": "McCulloch v. Maryland, 17 U.S. 316 (1819)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.95,
    },
    {
        "citation_text": "Gibbons v. Ogden, 22 U.S. 1 (1824)",
        "verification_source": "Justia",
        "verification_confidence": 0.94,
    },
    {
        "citation_text": "Griswold v. Connecticut, 381 U.S. 479 (1965)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.93,
    },
    {
        "citation_text": "Lawrence v. Texas, 539 U.S. 558 (2003)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.92,
    },
    {
        "citation_text": "Texas v. Johnson, 491 U.S. 397 (1989)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.91,
    },
    {
        "citation_text": "Shelley v. Kraemer, 334 U.S. 1 (1948)",
        "verification_source": "Justia",
        "verification_confidence": 0.90,
    },
    {
        "citation_text": "Regents of the University of California v. Bakke, 438 U.S. 265 (1978)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.89,
    },
    {
        "citation_text": "Furman v. Georgia, 408 U.S. 238 (1972)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.88,
    },
    {
        "citation_text": "Katz v. United States, 389 U.S. 347 (1967)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.87,
    },
    {
        "citation_text": "Engel v. Vitale, 370 U.S. 421 (1962)",
        "verification_source": "Justia",
        "verification_confidence": 0.86,
    },
    {
        "citation_text": "Schenck v. United States, 249 U.S. 47 (1919)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.85,
    },
    {
        "citation_text": "Heart of Atlanta Motel v. United States, 379 U.S. 241 (1964)",
        "verification_source": "FindLaw",
        "verification_confidence": 0.84,
    },
    {
        "citation_text": "Wisconsin v. Yoder, 406 U.S. 205 (1972)",
        "verification_source": "Google Scholar",
        "verification_confidence": 0.83,
    },
    {
        "citation_text": "Dobbs v. Jackson Women's Health Organization, 597 U.S. ___ (2022)",
        "verification_source": "Justia",
        "verification_confidence": 0.95,
    },
    {
        "citation_text": "United States v. Windsor, 570 U.S. 744 (2013)",
        "verification_source": "Leagle.com",
        "verification_confidence": 0.94,
    },
]


def populate_multitool_data():
    """Populate the multitool_confirmed_citations table with 33 sample citations."""
    try:
        # Connect to the database using the canonical path
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='multitool_confirmed_citations'"
        )
        if cursor.fetchone() is None:
            # Create the table if it doesn't exist
            cursor.execute(
                """
            CREATE TABLE multitool_confirmed_citations (
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
            logger.info("Created multitool_confirmed_citations table")

        # Clear existing data
        cursor.execute("DELETE FROM multitool_confirmed_citations")
        logger.info("Cleared existing data from multitool_confirmed_citations table")

        # Insert 33 sample citations
        for i, citation in enumerate(sample_citations):
            brief_url = f"https://example.com/brief{i+1}"
            context = f"Context for {citation['citation_text']}"
            verification_explanation = f"Citation found on {citation['verification_source']} with full text and details."

            cursor.execute(
                """
            INSERT INTO multitool_confirmed_citations 
            (citation_text, brief_url, context, verification_source, verification_confidence, verification_explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    citation["citation_text"],
                    brief_url,
                    context,
                    citation["verification_source"],
                    citation["verification_confidence"],
                    verification_explanation,
                ),
            )

        conn.commit()

        # Verify the data was added
        cursor.execute("SELECT COUNT(*) FROM multitool_confirmed_citations")
        count = cursor.fetchone()[0]
        logger.info(f"Added {count} citations to multitool_confirmed_citations table")

        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error populating multitool data: {e}")
        return False


if __name__ == "__main__":
    populate_multitool_data()
