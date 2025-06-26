-- PostgreSQL Database Schema for PDF Summarizer
-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS key_findings CASCADE;
DROP TABLE IF EXISTS keywords CASCADE;
DROP TABLE IF EXISTS category_scores CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Main documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    
    -- PDF Metadata
    pdf_title TEXT,
    pdf_author TEXT,
    pdf_filename VARCHAR(255),
    pdf_pages INTEGER,
    pdf_filepath TEXT,
    
    -- Structured Summary Fields
    title TEXT,
    authors TEXT,
    year_published INTEGER,
    journal TEXT,
    bibtex_citation TEXT,
    document_type VARCHAR(100),
    sample_size TEXT,
    method TEXT,
    prediction_model BOOLEAN,
    key_takeaways TEXT,
    
    -- Document Stats
    word_count INTEGER,
    processing_timestamp TIMESTAMP,
    
    -- Categorization
    primary_category VARCHAR(50),
    
    -- Full JSON storage for complex fields
    categories_json JSONB,
    key_findings_json JSONB,
    
    -- Search and indexing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords table (many-to-many relationship)
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Key findings table (one-to-many relationship)
CREATE TABLE key_findings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    finding_name VARCHAR(255) NOT NULL,
    finding_description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Category scores table (one-to-many relationship)
CREATE TABLE category_scores (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    score DECIMAL(3,2) NOT NULL CHECK (score >= 0 AND score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX idx_documents_primary_category ON documents(primary_category);
CREATE INDEX idx_documents_year_published ON documents(year_published);
CREATE INDEX idx_documents_journal ON documents(journal);
CREATE INDEX idx_documents_authors ON documents(authors);
CREATE INDEX idx_documents_processed_at ON documents(processed_at);
CREATE INDEX idx_documents_title ON documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_documents_key_takeaways ON documents USING gin(to_tsvector('english', key_takeaways));

CREATE INDEX idx_keywords_keyword ON keywords(keyword);
CREATE INDEX idx_keywords_document_id ON keywords(document_id);

CREATE INDEX idx_key_findings_document_id ON key_findings(document_id);
CREATE INDEX idx_key_findings_name ON key_findings(finding_name);

CREATE INDEX idx_category_scores_category ON category_scores(category);
CREATE INDEX idx_category_scores_score ON category_scores(score);
CREATE INDEX idx_category_scores_document_id ON category_scores(document_id);

-- Full-text search index
CREATE INDEX idx_documents_full_text ON documents USING gin(
    to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(authors, '') || ' ' || 
        COALESCE(journal, '') || ' ' || 
        COALESCE(key_takeaways, '') || ' ' ||
        COALESCE(method, '')
    )
);

-- Create view for easy querying
CREATE VIEW documents_view AS
SELECT 
    d.id,
    d.source_file,
    d.title,
    d.authors,
    d.year_published,
    d.journal,
    d.document_type,
    d.primary_category,
    d.word_count,
    d.processed_at,
    d.key_takeaways,
    array_agg(DISTINCT k.keyword ORDER BY k.keyword) as keywords,
    json_object_agg(cs.category, cs.score) as category_scores
FROM documents d
LEFT JOIN keywords k ON d.id = k.document_id
LEFT JOIN category_scores cs ON d.id = cs.document_id
GROUP BY d.id, d.source_file, d.title, d.authors, d.year_published, 
         d.journal, d.document_type, d.primary_category, d.word_count, 
         d.processed_at, d.key_takeaways;

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();