-- Esquema de la base de datos para la Biblioteca de Conocimiento Personal

-- Tabla de Contenidos
CREATE TABLE contenidos (
    id INTEGER PRIMARY KEY,
    contenido_texto TEXT NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    fecha_importacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fuente_id INTEGER,
    plataforma_id INTEGER,
    url_original TEXT,
    contexto TEXT,
    FOREIGN KEY (fuente_id) REFERENCES fuentes(id),
    FOREIGN KEY (plataforma_id) REFERENCES plataformas(id)
);

-- Tabla de Fuentes
CREATE TABLE fuentes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

-- Tabla de Plataformas
CREATE TABLE plataformas (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL
);

-- Tabla de Metadatos
CREATE TABLE metadatos (
    contenido_id INTEGER,
    clave TEXT,
    valor TEXT,
    PRIMARY KEY (contenido_id, clave),
    FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
);

-- Tabla de Relaciones entre Contenidos
CREATE TABLE contenido_relacion (
    contenido_id1 INTEGER,
    contenido_id2 INTEGER,
    tipo_relacion TEXT,
    fuerza_relacion FLOAT,
    PRIMARY KEY (contenido_id1, contenido_id2, tipo_relacion),
    FOREIGN KEY (contenido_id1) REFERENCES contenidos(id),
    FOREIGN KEY (contenido_id2) REFERENCES contenidos(id)
);

-- Tabla de Análisis
CREATE TABLE analisis (
    id INTEGER PRIMARY KEY,
    contenido_id INTEGER,
    tipo_analisis TEXT NOT NULL,
    resultado TEXT NOT NULL,
    fecha_analisis DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
);

-- Tabla de Estadísticas
CREATE TABLE estadisticas (
    id INTEGER PRIMARY KEY,
    entidad_id INTEGER,
    tipo_entidad TEXT NOT NULL,
    tipo_estadistica TEXT NOT NULL,
    valor TEXT NOT NULL,
    fecha_calculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_contenidos_fecha ON contenidos(fecha_creacion);
CREATE INDEX idx_contenidos_fuente ON contenidos(fuente_id);
CREATE INDEX idx_contenidos_plataforma ON contenidos(plataforma_id);
CREATE INDEX idx_analisis_contenido ON analisis(contenido_id);
CREATE INDEX idx_analisis_tipo ON analisis(tipo_analisis);
CREATE INDEX idx_estadisticas_entidad ON estadisticas(entidad_id, tipo_entidad);

-- Habilitar búsqueda de texto completo
CREATE VIRTUAL TABLE contenidos_fts USING fts5(
    contenido_texto,
    content='contenidos',
    content_rowid='id'
);

-- Trigger para mantener actualizada la tabla FTS
CREATE TRIGGER contenidos_ai AFTER INSERT ON contenidos BEGIN
    INSERT INTO contenidos_fts(rowid, contenido_texto) VALUES (new.id, new.contenido_texto);
END;

CREATE TRIGGER contenidos_ad AFTER DELETE ON contenidos BEGIN
    INSERT INTO contenidos_fts(contenidos_fts, rowid, contenido_texto) VALUES('delete', old.id, old.contenido_texto);
END;

CREATE TRIGGER contenidos_au AFTER UPDATE ON contenidos BEGIN
    INSERT INTO contenidos_fts(contenidos_fts, rowid, contenido_texto) VALUES('delete', old.id, old.contenido_texto);
    INSERT INTO contenidos_fts(rowid, contenido_texto) VALUES (new.id, new.contenido_texto);
END;
