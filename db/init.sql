CREATE TABLE pacientes (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE examenes (
    id SERIAL PRIMARY KEY,
    paciente_id INT NOT NULL,
    tipo_examen VARCHAR(20) CHECK (tipo_examen IN ('laboratorio', 'imagenologia')) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

-- Datos de prueba para probar el endpoint localmente
INSERT INTO pacientes (rut, nombre, email) VALUES
('12.345.678-9', 'Juan Perez', 'juan@email.com'),
('9.876.543-2', 'Maria Gonzalez', 'maria@email.com'),
('19.222.333-K', 'Pedro Silva', 'pedro@email.com');

INSERT INTO examenes (paciente_id, tipo_examen, nombre_archivo) VALUES
(1, 'laboratorio', 'lab_001.pdf'),
(1, 'imagenologia', 'rx_001.jpg'),
(2, 'laboratorio', 'lab_002.pdf'),
(2, 'imagenologia', 'tac_001.jpg'),
(3, 'laboratorio', 'lab_003.pdf'),
(3, 'laboratorio', 'lab_004.pdf');