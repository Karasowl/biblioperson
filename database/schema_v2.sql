-- Schema v2 para Biblioperson
-- Optimizado para almacenamiento dual: reconstrucción de documentos y búsqueda semántica

-- Tabla principal de documentos
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT NOT NULL,  -- SHA256 del archivo para detectar cambios
    file_type TEXT NOT NULL,  -- pdf, docx, epub, txt, md, json, ndjson
    file_size INTEGER,
    
    -- Metadatos del documento
    language TEXT DEFAULT 'es',
    publication_date TEXT,
    publisher TEXT,
    isbn TEXT,
    doi TEXT,
    tags TEXT,  -- JSON array de tags
    
    -- Metadatos de procesamiento
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_version TEXT DEFAULT '2.0',
    used_ocr BOOLEAN DEFAULT FALSE,
    ocr_confidence REAL,
    page_count INTEGER,
    
    -- Metadatos adicionales en JSON
    metadata TEXT DEFAULT '{}',
    
    -- Control
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Índices para búsqueda rápida
    INDEX idx_documents_title (title),
    INDEX idx_documents_author (author),
    INDEX idx_documents_file_type (file_type),
    INDEX idx_documents_active (is_active)
);

-- Tabla de bloques estructurales para reconstrucción
CREATE TABLE IF NOT EXISTS structural_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- Posición y estructura
    order_index INTEGER NOT NULL,  -- Orden en el documento
    parent_block_id INTEGER,  -- Para estructuras anidadas
    depth_level INTEGER DEFAULT 0,  -- Nivel de anidación
    
    -- Tipo y contenido
    block_type TEXT NOT NULL,  -- Title, NarrativeText, ListItem, Table, Image, etc.
    text_content TEXT NOT NULL,
    
    -- Metadatos del bloque
    style_info TEXT,  -- JSON con información de estilo (font, size, bold, etc.)
    position_info TEXT,  -- JSON con información de posición (page, x, y, width, height)
    
    -- Para elementos especiales
    image_path TEXT,  -- Para bloques de tipo Image
    table_data TEXT,  -- JSON para datos de tabla
    link_url TEXT,  -- Para enlaces
    
    -- Metadatos adicionales
    metadata TEXT DEFAULT '{}',
    
    -- Control
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_block_id) REFERENCES structural_blocks(id) ON DELETE SET NULL,
    
    -- Índices para reconstrucción eficiente
    INDEX idx_blocks_document (document_id),
    INDEX idx_blocks_order (document_id, order_index),
    INDEX idx_blocks_type (block_type),
    INDEX idx_blocks_parent (parent_block_id)
);

-- Tabla de chunks para búsqueda semántica
CREATE TABLE IF NOT EXISTS semantic_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- Identificación del chunk
    chunk_index INTEGER NOT NULL,
    chunk_id TEXT UNIQUE NOT NULL,  -- ID único del chunk
    
    -- Contenido
    text_content TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    
    -- Relación con bloques estructurales
    start_block_id INTEGER,  -- Primer bloque incluido en este chunk
    end_block_id INTEGER,    -- Último bloque incluido en este chunk
    
    -- Información de contexto
    chunk_profile TEXT,  -- narrative, poetry, technical, etc.
    previous_chunk_id INTEGER,  -- Para mantener continuidad
    next_chunk_id INTEGER,
    
    -- Embedding (almacenado como BLOB de floats)
    embedding BLOB,  -- Vector de embeddings serializado
    embedding_model TEXT,  -- Modelo usado para generar el embedding
    embedding_dimensions INTEGER,  -- Dimensiones del vector
    
    -- Metadatos para búsqueda
    metadata TEXT DEFAULT '{}',
    
    -- Control
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP,  -- Cuándo se generó el embedding
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (start_block_id) REFERENCES structural_blocks(id),
    FOREIGN KEY (end_block_id) REFERENCES structural_blocks(id),
    FOREIGN KEY (previous_chunk_id) REFERENCES semantic_chunks(id),
    FOREIGN KEY (next_chunk_id) REFERENCES semantic_chunks(id),
    
    -- Índices para búsqueda
    INDEX idx_chunks_document (document_id),
    INDEX idx_chunks_chunk_id (chunk_id),
    INDEX idx_chunks_profile (chunk_profile)
);

-- Tabla para versiones bíblicas (python-bible)
CREATE TABLE IF NOT EXISTS biblical_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_code TEXT UNIQUE NOT NULL,  -- ESV, RVR60, NVI, etc.
    version_name TEXT NOT NULL,
    language TEXT NOT NULL,
    copyright_info TEXT,
    
    -- Metadatos
    total_books INTEGER,
    total_chapters INTEGER,
    total_verses INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para libros bíblicos
CREATE TABLE IF NOT EXISTS biblical_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    book_number INTEGER NOT NULL,  -- Número canónico del libro
    book_name TEXT NOT NULL,
    book_abbrev TEXT NOT NULL,
    testament TEXT NOT NULL,  -- OLD, NEW
    
    -- Estadísticas
    chapter_count INTEGER,
    verse_count INTEGER,
    
    FOREIGN KEY (version_id) REFERENCES biblical_versions(id) ON DELETE CASCADE,
    
    UNIQUE(version_id, book_number),
    INDEX idx_biblical_books_version (version_id),
    INDEX idx_biblical_books_name (book_name)
);

-- Tabla para capítulos y versículos bíblicos
CREATE TABLE IF NOT EXISTS biblical_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    verse_text TEXT NOT NULL,
    
    -- Referencias cruzadas
    cross_references TEXT,  -- JSON array de referencias
    
    FOREIGN KEY (book_id) REFERENCES biblical_books(id) ON DELETE CASCADE,
    
    UNIQUE(book_id, chapter_number, verse_number),
    INDEX idx_verses_location (book_id, chapter_number, verse_number)
);

-- Tabla de configuración de usuario
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL DEFAULT 'default',
    
    -- Preferencias de chunking
    preferred_chunk_size INTEGER DEFAULT 750,
    preferred_overlap INTEGER DEFAULT 200,
    
    -- Preferencias de búsqueda
    search_result_limit INTEGER DEFAULT 20,
    rerank_results BOOLEAN DEFAULT TRUE,
    
    -- Preferencias de lectura
    preferred_font_size INTEGER DEFAULT 16,
    preferred_theme TEXT DEFAULT 'light',
    
    -- Configuración de embeddings
    embedding_backend TEXT DEFAULT 'local',  -- local, openai
    
    -- Metadatos
    config_json TEXT DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de búsquedas (para analytics)
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_embedding BLOB,
    result_count INTEGER,
    top_results TEXT,  -- JSON array de chunk_ids
    
    -- Métricas
    search_duration_ms INTEGER,
    rerank_duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_search_history_date (created_at)
);

-- Vistas útiles

-- Vista de documentos con estadísticas
CREATE VIEW IF NOT EXISTS document_stats AS
SELECT 
    d.id,
    d.title,
    d.author,
    d.file_type,
    COUNT(DISTINCT sb.id) as block_count,
    COUNT(DISTINCT sc.id) as chunk_count,
    MAX(sb.order_index) as total_blocks,
    d.processed_at,
    d.file_size
FROM documents d
LEFT JOIN structural_blocks sb ON d.id = sb.document_id
LEFT JOIN semantic_chunks sc ON d.id = sc.document_id
WHERE d.is_active = TRUE
GROUP BY d.id;

-- Vista de chunks con contexto completo
CREATE VIEW IF NOT EXISTS chunks_with_context AS
SELECT 
    sc.id,
    sc.chunk_id,
    sc.text_content,
    sc.chunk_profile,
    d.title as document_title,
    d.author as document_author,
    d.file_type,
    sc.chunk_index,
    sc.embedding IS NOT NULL as has_embedding
FROM semantic_chunks sc
JOIN documents d ON sc.document_id = d.id
WHERE d.is_active = TRUE;

-- Triggers para actualizar timestamps
CREATE TRIGGER update_documents_timestamp 
AFTER UPDATE ON documents
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_user_config_timestamp 
AFTER UPDATE ON user_config
BEGIN
    UPDATE user_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 