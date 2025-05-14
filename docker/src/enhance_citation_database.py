"""
Enhance Citation Database

This script enhances the CaseStrainer database by:
1. Adding context (200 characters) around each citation
2. Adding links to the source files containing the citations
3. Extracting more detailed citation information (parties, year, court)
"""

import os
import sys
import json
import logging
import sqlite3
import re
import PyPDF2
from pathlib import Path
from datetime import datetime
import shutil
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.expanduser('~'), 'Documents', 'enhance_citations.log'))
    ]
)
logger = logging.getLogger("citation_enhancer")

# Constants
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(REPO_DIR, "citations.db")
USER_DOCS = os.path.join(os.path.expanduser('~'), 'Documents')
RESULTS_DIR = os.path.join(USER_DOCS, "WA_Briefs_Results")
EXTRACTED_DIR = os.path.join(RESULTS_DIR, "extracted_text")
BRIEFS_DIR = "D:\\CaseStrainer\\downloaded_briefs"
WEB_BASE_URL = "https://wolf.law.uw.edu/casestrainer/briefs/"

# Backup database before making changes
BACKUP_DIR = os.path.join(USER_DOCS, "CaseStrainer_Backups", datetime.now().strftime("%Y%m%d_%H%M%S"))

def backup_database():
    """Backup the database before making changes."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory: {BACKUP_DIR}")
    
    backup_path = os.path.join(BACKUP_DIR, "citations.db")
    shutil.copy2(DB_PATH, backup_path)
    logger.info(f"Backed up database to {backup_path}")

def get_citations_from_database():
    """Get all citations from the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all citations
        cursor.execute("SELECT id, citation_text, source, source_document FROM citations")
        rows = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert to dictionaries
        citations = []
        for row in rows:
            citations.append({
                "id": row[0],
                "citation_text": row[1],
                "source": row[2],
                "source_document": row[3]
            })
        
        return citations
    
    except Exception as e:
        logger.error(f"Error getting citations from database: {e}")
        return []

def find_text_files():
    """Find all text files in the extracted text directory."""
    text_files = {}
    
    # Check extracted text directory
    if os.path.exists(EXTRACTED_DIR):
        for file in os.listdir(EXTRACTED_DIR):
            if file.endswith(".txt"):
                file_path = os.path.join(EXTRACTED_DIR, file)
                text_files[file] = file_path
    
    return text_files

def find_pdf_files():
    """Find all PDF files in the briefs directory."""
    pdf_files = {}
    
    # Check briefs directory
    if os.path.exists(BRIEFS_DIR):
        for root, dirs, files in os.walk(BRIEFS_DIR):
            for file in files:
                if file.endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    pdf_files[file] = file_path
    
    return pdf_files

def extract_citation_context(text, citation, context_chars=200):
    """Extract context around a citation."""
    if not text or not citation:
        return ""
    
    try:
        # Find the citation in the text
        citation_index = text.find(citation)
        
        if citation_index == -1:
            # Try with a more flexible search
            citation_parts = re.split(r'[\s\.,;]', citation)
            for part in citation_parts:
                if len(part) > 3:  # Only use meaningful parts
                    part_index = text.find(part)
                    if part_index != -1:
                        citation_index = part_index
                        break
        
        if citation_index == -1:
            return ""
        
        # Get context around the citation
        start_index = max(0, citation_index - context_chars // 2)
        end_index = min(len(text), citation_index + len(citation) + context_chars // 2)
        
        # Adjust to not cut words
        while start_index > 0 and text[start_index] != ' ' and text[start_index] != '\n':
            start_index -= 1
        
        while end_index < len(text) - 1 and text[end_index] != ' ' and text[end_index] != '\n':
            end_index += 1
        
        context = text[start_index:end_index].strip()
        
        # Highlight the citation in the context
        highlighted_context = context.replace(citation, f"**{citation}**")
        
        return highlighted_context
    
    except Exception as e:
        logger.error(f"Error extracting context for citation '{citation}': {e}")
        return ""

def parse_citation(citation_text):
    """Parse citation to extract parties, year, court, etc."""
    if not citation_text:
        return {}
    
    result = {
        "parties": "",
        "year": "",
        "court": "",
        "volume": "",
        "reporter": "",
        "page": ""
    }
    
    try:
        # Extract volume, reporter, and page
        volume_reporter_page = re.search(r'(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)', citation_text)
        if volume_reporter_page:
            result["volume"] = volume_reporter_page.group(1)
            result["reporter"] = volume_reporter_page.group(2).strip()
            result["page"] = volume_reporter_page.group(3)
        
        # Extract year
        year = re.search(r'\((\d{4})\)', citation_text)
        if year:
            result["year"] = year.group(1)
        
        # Extract court
        if "Wn." in citation_text or "Wash." in citation_text:
            if "App." in citation_text:
                result["court"] = "Washington Court of Appeals"
            else:
                result["court"] = "Washington Supreme Court"
        elif "U.S." in citation_text:
            result["court"] = "United States Supreme Court"
        elif "F." in citation_text:
            if "Supp." in citation_text:
                result["court"] = "United States District Court"
            else:
                result["court"] = "United States Court of Appeals"
        
        # Extract parties
        parties = re.search(r'([A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+)', citation_text)
        if parties:
            result["parties"] = parties.group(1)
        
        return result
    
    except Exception as e:
        logger.error(f"Error parsing citation '{citation_text}': {e}")
        return result

def create_file_link(source_document):
    """Create a web link to the source file."""
    if not source_document:
        return ""
    
    try:
        # Create a sanitized filename for the web link
        sanitized_name = re.sub(r'[^\w\-\.]', '_', os.path.basename(source_document))
        
        # Create the web link
        web_link = f"{WEB_BASE_URL}{sanitized_name}"
        
        return web_link
    
    except Exception as e:
        logger.error(f"Error creating file link for '{source_document}': {e}")
        return ""

def update_citation_in_database(citation_id, context, file_link, citation_details):
    """Update a citation in the database with context and file link."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the context column exists
        cursor.execute("PRAGMA table_info(citations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = {
            "context": "TEXT",
            "file_link": "TEXT",
            "parties": "TEXT",
            "year": "TEXT",
            "court": "TEXT",
            "volume": "TEXT",
            "reporter": "TEXT",
            "page": "TEXT"
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE citations ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added new column '{col_name}' to the database")
        
        # Update the citation
        cursor.execute(
            """
            UPDATE citations
            SET context = ?, file_link = ?, parties = ?, year = ?, court = ?, volume = ?, reporter = ?, page = ?
            WHERE id = ?
            """,
            (
                context,
                file_link,
                citation_details.get("parties", ""),
                citation_details.get("year", ""),
                citation_details.get("court", ""),
                citation_details.get("volume", ""),
                citation_details.get("reporter", ""),
                citation_details.get("page", ""),
                citation_id
            )
        )
        
        # Commit the changes
        conn.commit()
        
        # Close the connection
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating citation {citation_id} in database: {e}")
        return False

def copy_briefs_to_web_directory():
    """Copy briefs to a web-accessible directory."""
    try:
        # Create web directory if it doesn't exist
        web_dir = os.path.join(REPO_DIR, "static", "briefs")
        if not os.path.exists(web_dir):
            os.makedirs(web_dir)
            logger.info(f"Created web directory: {web_dir}")
        
        # Copy PDF files to web directory
        pdf_files = find_pdf_files()
        copied_count = 0
        
        for file_name, file_path in pdf_files.items():
            sanitized_name = re.sub(r'[^\w\-\.]', '_', file_name)
            web_path = os.path.join(web_dir, sanitized_name)
            
            if not os.path.exists(web_path):
                shutil.copy2(file_path, web_path)
                copied_count += 1
        
        logger.info(f"Copied {copied_count} briefs to web directory")
        
        # Create a D: drive web directory if needed
        d_drive_web_dir = "D:\\CaseStrainer\\static\\briefs"
        if os.path.exists("D:\\CaseStrainer"):
            if not os.path.exists(d_drive_web_dir):
                os.makedirs(d_drive_web_dir)
                logger.info(f"Created D: drive web directory: {d_drive_web_dir}")
            
            # Copy files to D: drive web directory
            for file_name, file_path in pdf_files.items():
                sanitized_name = re.sub(r'[^\w\-\.]', '_', file_name)
                d_web_path = os.path.join(d_drive_web_dir, sanitized_name)
                
                if not os.path.exists(d_web_path):
                    shutil.copy2(file_path, d_web_path)
            
            logger.info(f"Copied briefs to D: drive web directory")
        
        return True
    
    except Exception as e:
        logger.error(f"Error copying briefs to web directory: {e}")
        return False

def main():
    """Main function to enhance the citation database."""
    logger.info("Starting enhancement of citation database")
    
    # Backup the database
    backup_database()
    
    # Find text files
    text_files = find_text_files()
    logger.info(f"Found {len(text_files)} text files")
    
    # Find PDF files
    pdf_files = find_pdf_files()
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Copy briefs to web directory
    copy_briefs_to_web_directory()
    
    # Get citations from the database
    citations = get_citations_from_database()
    logger.info(f"Retrieved {len(citations)} citations from the database")
    
    # Process each citation
    updated_count = 0
    
    for citation in tqdm(citations, desc="Enhancing citations"):
        citation_id = citation["id"]
        citation_text = citation["citation_text"]
        source = citation["source"]
        source_document = citation["source_document"]
        
        # Find the text file for this citation
        text_content = ""
        for file_name, file_path in text_files.items():
            if source and source in file_name:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
                break
        
        # If no text file found, try to extract from PDF
        if not text_content and source_document:
            pdf_path = ""
            for file_name, file_path in pdf_files.items():
                if source_document and os.path.basename(source_document) in file_name:
                    pdf_path = file_path
                    break
            
            if pdf_path:
                try:
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page_num in range(len(pdf_reader.pages)):
                            text_content += pdf_reader.pages[page_num].extract_text() + "\n"
                except Exception as e:
                    logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        
        # Extract context
        context = extract_citation_context(text_content, citation_text)
        
        # Create file link
        file_link = create_file_link(source_document)
        
        # Parse citation
        citation_details = parse_citation(citation_text)
        
        # Update the database
        if update_citation_in_database(citation_id, context, file_link, citation_details):
            updated_count += 1
    
    logger.info(f"Enhanced {updated_count} citations in the database")
    logger.info("Finished enhancing citation database")

if __name__ == "__main__":
    main()
