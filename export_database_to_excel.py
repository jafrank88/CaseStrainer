#!/usr/bin/env python3
"""
Export CaseStrainer Database to Excel

This script exports the SQLite database to an Excel (.xlsx) file with proper formatting.
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import json

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def export_database_to_excel():
    """Export the SQLite database to Excel format."""
    
    print("=" * 60)
    print("CaseStrainer Database Export to Excel")
    print("=" * 60)
    
    # Database path
    db_path = "src/citations.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"casestrainer_database_export_{timestamp}.xlsx"
    
    print(f"📊 Exporting database: {db_path}")
    print(f"📁 Output file: {output_file}")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Get list of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
        print()
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # Export each table to a separate sheet
            for table_name in tables:
                print(f"📝 Exporting table: {table_name}")
                
                # Read table data
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                
                # Clean up data for better Excel display
                if not df.empty:
                    # Convert JSON columns to readable format
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            # Try to parse JSON and make it readable
                            try:
                                df[col] = df[col].apply(lambda x: 
                                    json.dumps(json.loads(x), indent=2) if x and isinstance(x, str) and x.startswith('{') else x
                                )
                            except:
                                pass
                    
                    # Format datetime columns
                    datetime_columns = ['created_at', 'updated_at', 'verified_at', 'date_added']
                    for col in datetime_columns:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='ignore')
                    
                    # Write to Excel with formatting
                    df.to_excel(writer, sheet_name=table_name, index=False)
                    
                    # Get the worksheet for formatting
                    worksheet = writer.sheets[table_name]
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        # Set column width (with some padding)
                        adjusted_width = min(max_length + 2, 50)  # Max width of 50
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    print(f"   ✅ Exported {len(df)} rows")
                else:
                    print(f"   ⚠️  Table is empty")
        
        # Create a summary sheet
        print("\n📊 Creating summary sheet...")
        summary_data = []
        
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            summary_data.append({
                'Table Name': table_name,
                'Row Count': row_count
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Add database info
        cursor.execute("PRAGMA table_info(citations)")
        citation_columns = cursor.fetchall()
        
        column_info = []
        for col in citation_columns:
            column_info.append({
                'Column Name': col[1],
                'Data Type': col[2],
                'Not Null': bool(col[3]),
                'Default Value': col[4],
                'Primary Key': bool(col[5])
            })
        
        column_df = pd.DataFrame(column_info)
        column_df.to_excel(writer, sheet_name='Schema_Info', index=False)
        
        conn.close()
        
        print(f"\n🎉 Export completed successfully!")
        print(f"📁 File saved as: {output_file}")
        
        # Show file size
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        print(f"📏 File size: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

def create_sample_analysis():
    """Create a sample analysis of the database."""
    
    print("\n" + "=" * 60)
    print("Database Analysis")
    print("=" * 60)
    
    db_path = "src/citations.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Basic statistics
        cursor.execute("SELECT COUNT(*) FROM citations")
        total_citations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 1")
        verified_citations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 0")
        unverified_citations = cursor.fetchone()[0]
        
        # Source distribution
        cursor.execute("SELECT source, COUNT(*) FROM citations GROUP BY source ORDER BY COUNT(*) DESC")
        source_distribution = cursor.fetchall()
        
        # Year distribution
        cursor.execute("SELECT year, COUNT(*) FROM citations WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC LIMIT 10")
        year_distribution = cursor.fetchall()
        
        print(f"📊 Total Citations: {total_citations:,}")
        print(f"✅ Verified: {verified_citations:,} ({verified_citations/total_citations*100:.1f}%)")
        print(f"❌ Unverified: {unverified_citations:,} ({unverified_citations/total_citations*100:.1f}%)")
        
        print(f"\n📈 Top Sources:")
        for source, count in source_distribution[:5]:
            print(f"   {source}: {count:,}")
        
        print(f"\n📅 Recent Years:")
        for year, count in year_distribution:
            print(f"   {year}: {count:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def main():
    """Main function."""
    
    # Export database
    success = export_database_to_excel()
    
    if success:
        # Show analysis
        create_sample_analysis()
        
        print(f"\n" + "=" * 60)
        print("EXPORT COMPLETE!")
        print("=" * 60)
        print("You can now open the Excel file to view your database data.")
        print("The file contains multiple sheets:")
        print("  • Citations - Main citation data")
        print("  • Cache_Stats - Cache performance statistics")
        print("  • Summary - Overview of all tables")
        print("  • Schema_Info - Database structure information")
    else:
        print("Export failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 