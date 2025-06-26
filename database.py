import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from config import Config
from rich.console import Console

console = Console()

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.connect()
    
    def connect(self):
        """Initialize database connection pool"""
        try:
            if Config.DATABASE_URL:
                self.pool = SimpleConnectionPool(
                    1, 20,  # min and max connections
                    Config.DATABASE_URL
                )
            else:
                self.pool = SimpleConnectionPool(
                    1, 20,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    database=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD
                )
            console.print("[green]Database connected successfully[/green]")
        except Exception as e:
            console.print(f"[red]Database connection failed: {e}[/red]")
            self.pool = None
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.pool:
            return self.pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query with optional parameters"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        except Exception as e:
            conn.rollback()
            console.print(f"[red]Database query error: {e}[/red]")
            return None
        finally:
            self.return_connection(conn)
    
    def insert_document(self, result: Dict) -> Optional[int]:
        """Insert a document and related data into the database"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                # Extract data from result
                metadata = result.get('metadata', {})
                summary = result.get('summary', {})
                keywords = result.get('keywords', [])
                categories = result.get('categories', {})
                
                # Insert main document
                insert_doc_query = """
                INSERT INTO documents (
                    source_file, processed_at, pdf_title, pdf_author, pdf_filename, 
                    pdf_pages, pdf_filepath, title, authors, year_published, journal,
                    bibtex_citation, document_type, sample_size, method, prediction_model,
                    key_takeaways, word_count, processing_timestamp, primary_category,
                    categories_json, key_findings_json
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """
                
                # Prepare document data
                doc_data = (
                    result.get('source_file', metadata.get('filename', '')),
                    datetime.fromisoformat(result.get('processed_at', datetime.now().isoformat())),
                    metadata.get('title'),
                    metadata.get('author'),
                    metadata.get('filename'),
                    metadata.get('pages'),
                    metadata.get('filepath'),
                    summary.get('Title') if isinstance(summary, dict) else None,
                    summary.get('Author(s)') if isinstance(summary, dict) else None,
                    summary.get('Year Published') if isinstance(summary, dict) else None,
                    summary.get('Journal') if isinstance(summary, dict) else None,
                    summary.get('BibTeX Citation') if isinstance(summary, dict) else None,
                    summary.get('Type') if isinstance(summary, dict) else None,
                    summary.get('Sample Size') if isinstance(summary, dict) else None,
                    summary.get('Method') if isinstance(summary, dict) else None,
                    summary.get('Prediction Model') == 'yes' if isinstance(summary, dict) else None,
                    summary.get('Key Takeaways') if isinstance(summary, dict) else str(summary),
                    result.get('word_count'),
                    datetime.fromisoformat(result.get('processed_at', datetime.now().isoformat())),
                    result.get('primary_category'),
                    json.dumps(categories),
                    json.dumps(summary.get('Key Findings', {}) if isinstance(summary, dict) else {})
                )
                
                cur.execute(insert_doc_query, doc_data)
                doc_id = cur.fetchone()[0]
                
                # Insert keywords
                if keywords:
                    insert_keyword_query = "INSERT INTO keywords (document_id, keyword) VALUES (%s, %s)"
                    keyword_data = [(doc_id, keyword) for keyword in keywords]
                    cur.executemany(insert_keyword_query, keyword_data)
                
                # Insert category scores
                if categories:
                    insert_category_query = "INSERT INTO category_scores (document_id, category, score) VALUES (%s, %s, %s)"
                    category_data = [(doc_id, category, score) for category, score in categories.items()]
                    cur.executemany(insert_category_query, category_data)
                
                # Insert key findings
                if isinstance(summary, dict) and 'Key Findings' in summary:
                    findings = summary['Key Findings']
                    if isinstance(findings, dict):
                        insert_finding_query = "INSERT INTO key_findings (document_id, finding_name, finding_description) VALUES (%s, %s, %s)"
                        finding_data = [(doc_id, name, desc) for name, desc in findings.items()]
                        cur.executemany(insert_finding_query, finding_data)
                
                conn.commit()
                console.print(f"[green]Document inserted with ID: {doc_id}[/green]")
                return doc_id
                
        except Exception as e:
            conn.rollback()
            console.print(f"[red]Error inserting document: {e}[/red]")
            return None
        finally:
            self.return_connection(conn)
    
    def search_documents(self, 
                        query: str = None,
                        category: str = None,
                        year_from: int = None,
                        year_to: int = None,
                        author: str = None,
                        journal: str = None,
                        limit: int = 50) -> List[Dict]:
        """Search documents with various filters"""
        
        where_conditions = []
        params = []
        
        base_query = """
        SELECT 
            d.id, d.title, d.authors, d.year_published, d.journal, 
            d.primary_category, d.key_takeaways, d.processed_at,
            d.word_count, d.source_file,
            array_agg(DISTINCT k.keyword) as keywords
        FROM documents d
        LEFT JOIN keywords k ON d.id = k.document_id
        """
        
        if query:
            where_conditions.append("to_tsvector('english', COALESCE(d.title, '') || ' ' || COALESCE(d.key_takeaways, '')) @@ plainto_tsquery('english', %s)")
            params.append(query)
        
        if category:
            where_conditions.append("d.primary_category = %s")
            params.append(category)
        
        if year_from:
            where_conditions.append("d.year_published >= %s")
            params.append(year_from)
        
        if year_to:
            where_conditions.append("d.year_published <= %s")
            params.append(year_to)
        
        if author:
            where_conditions.append("d.authors ILIKE %s")
            params.append(f"%{author}%")
        
        if journal:
            where_conditions.append("d.journal ILIKE %s")
            params.append(f"%{journal}%")
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        base_query += """
        GROUP BY d.id, d.title, d.authors, d.year_published, d.journal, 
                 d.primary_category, d.key_takeaways, d.processed_at,
                 d.word_count, d.source_file
        ORDER BY d.processed_at DESC
        LIMIT %s
        """
        params.append(limit)
        
        return self.execute_query(base_query, tuple(params), fetch=True) or []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Total documents
        result = self.execute_query("SELECT COUNT(*) as count FROM documents", fetch=True)
        stats['total_documents'] = result[0]['count'] if result else 0
        
        # Documents by category
        result = self.execute_query("""
            SELECT primary_category, COUNT(*) as count 
            FROM documents 
            GROUP BY primary_category 
            ORDER BY count DESC
        """, fetch=True)
        stats['by_category'] = {row['primary_category']: row['count'] for row in result} if result else {}
        
        # Documents by year
        result = self.execute_query("""
            SELECT year_published, COUNT(*) as count 
            FROM documents 
            WHERE year_published IS NOT NULL
            GROUP BY year_published 
            ORDER BY year_published DESC
            LIMIT 10
        """, fetch=True)
        stats['by_year'] = {row['year_published']: row['count'] for row in result} if result else {}
        
        # Top journals
        result = self.execute_query("""
            SELECT journal, COUNT(*) as count 
            FROM documents 
            WHERE journal IS NOT NULL AND journal != 'Not specified'
            GROUP BY journal 
            ORDER BY count DESC
            LIMIT 10
        """, fetch=True)
        stats['top_journals'] = {row['journal']: row['count'] for row in result} if result else {}
        
        return stats
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get a complete document by ID"""
        query = """
        SELECT 
            d.*, 
            array_agg(DISTINCT k.keyword) as keywords,
            json_object_agg(cs.category, cs.score) FILTER (WHERE cs.category IS NOT NULL) as category_scores,
            array_agg(json_build_object('name', kf.finding_name, 'description', kf.finding_description)) 
                FILTER (WHERE kf.finding_name IS NOT NULL) as key_findings
        FROM documents d
        LEFT JOIN keywords k ON d.id = k.document_id
        LEFT JOIN category_scores cs ON d.id = cs.document_id
        LEFT JOIN key_findings kf ON d.id = kf.document_id
        WHERE d.id = %s
        GROUP BY d.id
        """
        
        result = self.execute_query(query, (doc_id,), fetch=True)
        return result[0] if result else None
    
    def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.closeall()
            console.print("[yellow]Database connections closed[/yellow]")