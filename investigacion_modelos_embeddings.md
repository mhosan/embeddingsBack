# Investigación: Modelos de Embeddings Gratuitos en Hugging Face

## ✅ Compatibilidad con InferenceClient

**TODOS los modelos investigados son compatibles con `InferenceClient.feature_extraction()`**

El `InferenceClient` de Hugging Face soporta la tarea de `feature_extraction` (generación de embeddings) para todos los modelos mencionados en esta investigación:

- ✅ **BAAI/bge-small-en-v1.5** (modelo actual)
- ✅ **sentence-transformers/all-MiniLM-L6-v2**
- ✅ **sentence-transformers/all-mpnet-base-v2**
- ✅ **intfloat/e5-large-v2**
- ✅ **BAAI/bge-base-en-v1.5**
- ✅ **BAAI/bge-m3**

**Uso**: Simplemente cambia el parámetro `model` en la llamada a `client.feature_extraction()`:

```python
# Ejemplo de cambio de modelo
result = client.feature_extraction(
    text=texts,
    model="sentence-transformers/all-MiniLM-L6-v2"  # Cambiar aquí
)
```

**Nota importante**: Al cambiar de modelo, también debes actualizar `MODEL_DIMENSIONS` en `constants.py` para que coincida con las dimensiones del nuevo modelo.

---

## ⚠️ ADVERTENCIA CRÍTICA: Cambio de Dimensiones en Supabase

### Problema con pgvector

**Si cambias a un modelo con dimensiones diferentes (ej: de 384 a 768), HABRÁ PROBLEMAS con la base de datos Supabase.**

La columna `embedding` en tu tabla `documents` está definida como `vector(384)` en PostgreSQL/pgvector. Esto significa:

- ❌ **NO puedes insertar** vectores de 768 dimensiones en una columna `vector(384)`
- ❌ **NO puedes cambiar** las dimensiones de una columna existente con un simple `ALTER COLUMN`
- ❌ **Los datos existentes** (embeddings de 384 dimensiones) NO son compatibles con modelos de 768 dimensiones

### Opciones si Quieres Cambiar de Dimensiones

#### **Opción 1: Crear Nueva Columna y Migrar** (Recomendado)

```sql
-- 1. Agregar nueva columna con las nuevas dimensiones
ALTER TABLE documents ADD COLUMN embedding_768 vector(768);

-- 2. Regenerar embeddings para todos los documentos existentes
-- (esto debe hacerse desde tu aplicación Python)

-- 3. Opcional: Eliminar la columna antigua
ALTER TABLE documents DROP COLUMN embedding;

-- 4. Renombrar la nueva columna
ALTER TABLE documents RENAME COLUMN embedding_768 TO embedding;
```

**Implicaciones:**
- ✅ Mantiene los datos existentes
- ⚠️ Requiere **regenerar TODOS los embeddings** con el nuevo modelo
- ⚠️ Puede ser costoso en tiempo si tienes muchos documentos

#### **Opción 2: Crear Nueva Tabla** (Más seguro)

```sql
-- Crear nueva tabla con las nuevas dimensiones
CREATE TABLE documents_v2 (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),  -- Nueva dimensión
    metadata JSONB,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Crear índice para búsqueda vectorial
CREATE INDEX ON documents_v2 USING ivfflat (embedding vector_cosine_ops);
```

**Implicaciones:**
- ✅ Mantiene la tabla original intacta (backup automático)
- ✅ Puedes comparar resultados entre modelos
- ⚠️ Requiere actualizar el código para usar la nueva tabla

#### **Opción 3: Borrar Todo y Empezar de Cero** (Más simple, pero destructivo)

```sql
-- ⚠️ ESTO BORRA TODOS LOS DATOS
DROP TABLE documents;

-- Crear tabla nueva con las nuevas dimensiones
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),  -- Nueva dimensión
    metadata JSONB,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

**Implicaciones:**
- ❌ **PIERDES TODOS LOS DATOS EXISTENTES**
- ✅ Más simple y rápido
- ✅ Útil si estás en fase de pruebas

### Modelos que NO Requieren Cambios en la BD

Estos modelos usan **384 dimensiones** (igual que el actual):

- ✅ **sentence-transformers/all-MiniLM-L6-v2** (384 dims)
- ✅ **BAAI/bge-small-en-v1.5** (384 dims) ← Modelo actual

**Puedes cambiar entre estos modelos SIN modificar la base de datos.**

### Modelos que SÍ Requieren Cambios en la BD

Estos modelos usan dimensiones diferentes:

- ⚠️ **sentence-transformers/all-mpnet-base-v2** (768 dims)
- ⚠️ **BAAI/bge-base-en-v1.5** (768 dims)
- ⚠️ **intfloat/e5-large-v2** (1024 dims)
- ⚠️ **BAAI/bge-m3** (1024 dims)

**Requieren migración de la base de datos antes de usarlos.**

### Recomendación

Si quieres probar un modelo con diferentes dimensiones:

1. **Opción segura**: Usa la **Opción 2** (nueva tabla) para no perder datos
2. **Opción rápida**: Si estás en desarrollo/pruebas, usa la **Opción 3** (borrar y recrear)
3. **Para producción**: Usa la **Opción 1** (migrar columna) con un script de migración bien testeado

---

## Modelo Actual
**BAAI/bge-small-en-v1.5**
- **Dimensiones**: 384
- **Parámetros**: 33.4 millones
- **Tamaño**: ~134 MB
- **Rendimiento**: Estado del arte en MTEB y C-MTEB benchmarks para su categoría
- **Casos de uso**: Búsqueda semántica, clustering, clasificación de texto, recuperación densa

---

## Alternativas Gratuitas en Hugging Face

### 1. **sentence-transformers/all-MiniLM-L6-v2** ⚡ (MÁS RÁPIDO)

| Característica | Valor |
|----------------|-------|
| **Dimensiones** | 384 |
| **Parámetros** | 22 millones |
| **Tamaño** | ~22 MB |
| **Velocidad** | ~14,200 oraciones/segundo (CPU) |
| **Latencia** | 14.7 ms por 1K tokens |

**Ventajas:**
- ✅ **5x más rápido** que modelos como all-mpnet-base-v2
- ✅ **Más liviano** (22M vs 33.4M parámetros)
- ✅ Excelente para aplicaciones de alta demanda y baja latencia
- ✅ Ideal para APIs en tiempo real y chatbots

**Desventajas:**
- ⚠️ Precisión de recuperación **5-8% menor** que modelos más grandes
- ⚠️ Optimizado para textos cortos (128-256 tokens)
- ⚠️ Rendimiento puede degradarse con documentos largos o ruidosos

**Comparación con bge-small-en-v1.5:**
- 🔴 **Menos preciso** en tareas de recuperación y clasificación
- 🟢 **Más rápido** en inferencia
- 🟢 **Más liviano** en memoria

---

### 2. **sentence-transformers/all-mpnet-base-v2** 🎯 (EQUILIBRADO)

| Característica | Valor |
|----------------|-------|
| **Dimensiones** | 768 |
| **Parámetros** | ~110 millones |
| **Tamaño** | ~420 MB |

**Ventajas:**
- ✅ Rendimiento sólido en tareas de similitud de texto
- ✅ Ampliamente usado y probado en producción
- ✅ Mayor dimensionalidad (768 vs 384)

**Desventajas:**
- ⚠️ **Más lento** que all-MiniLM-L6-v2
- ⚠️ **Más pesado** (110M vs 33.4M parámetros)
- ⚠️ Generalmente **superado por BGE** en benchmarks MTEB

**Comparación con bge-small-en-v1.5:**
- 🔴 **Menos preciso** en MTEB
- 🔴 **Más pesado** (3.3x más parámetros)
- 🟡 Dimensiones más altas (768 vs 384)

---

### 3. **intfloat/e5-large-v2** 💪 (MÁS POTENTE - pero más pesado)

| Característica | Valor |
|----------------|-------|
| **Dimensiones** | 1024 |
| **Parámetros** | ~335 millones |
| **Tamaño** | ~1.34 GB |

**Ventajas:**
- ✅ **Mejor rendimiento** que all-mpnet-base-v2
- ✅ Optimizado para múltiples idiomas
- ✅ Alta dimensionalidad (1024)

**Desventajas:**
- ⚠️ **Mucho más lento** debido al tamaño
- ⚠️ **10x más pesado** que bge-small-en-v1.5
- ⚠️ Mayor consumo de recursos

**Comparación con bge-small-en-v1.5:**
- 🟢 **Más preciso** en benchmarks
- 🔴 **Mucho más lento** y pesado
- 🔴 **10x más parámetros** (335M vs 33.4M)

---

### 4. **BAAI/bge-base-en-v1.5** 📈 (VERSIÓN MEJORADA DEL MISMO MODELO)

| Característica | Valor |
|----------------|-------|
| **Dimensiones** | 768 |
| **Parámetros** | ~109 millones |
| **Tamaño** | ~438 MB |

**Ventajas:**
- ✅ **Mejor rendimiento** que bge-small-en-v1.5
- ✅ Misma familia BGE (fácil migración)
- ✅ Mayor dimensionalidad (768 vs 384)
- ✅ Excelente en MTEB leaderboard

**Desventajas:**
- ⚠️ **3.3x más pesado** que bge-small
- ⚠️ Más lento en inferencia

**Comparación con bge-small-en-v1.5:**
- 🟢 **Más preciso** (versión base del mismo modelo)
- 🔴 **Más pesado** (109M vs 33.4M parámetros)
- 🟡 Mayor dimensionalidad requiere más espacio en BD

---

### 5. **BAAI/bge-m3** 🌍 (MULTILINGÜE Y MULTIFUNCIONAL)

| Característica | Valor |
|----------------|-------|
| **Dimensiones** | 1024 |
| **Parámetros** | ~567 millones |
| **Idiomas** | 100+ |
| **Tokens máximos** | 8192 |

**Ventajas:**
- ✅ **Multilingüe** (100+ idiomas)
- ✅ **Multi-granularidad** (hasta 8192 tokens)
- ✅ **Multi-funcional** (recuperación densa, léxica, multi-vector)
- ✅ Muy versátil para escenarios complejos

**Desventajas:**
- ⚠️ **Muy pesado** (567M parámetros)
- ⚠️ Overkill si solo necesitas inglés
- ⚠️ Mucho más lento

**Comparación con bge-small-en-v1.5:**
- 🟢 **Mucho más potente** y versátil
- 🔴 **17x más pesado** (567M vs 33.4M)
- 🟡 Solo útil si necesitas multilingüismo

---

## Recomendaciones por Caso de Uso

### ✅ **Mantener BAAI/bge-small-en-v1.5** si:
- Necesitas un **balance óptimo** entre rendimiento y velocidad
- Tu aplicación es principalmente en **inglés**
- Quieres **estado del arte** en su categoría de tamaño
- Tienes recursos limitados pero necesitas buena precisión

### 🔄 **Cambiar a sentence-transformers/all-MiniLM-L6-v2** si:
- La **velocidad es crítica** (APIs de alta demanda)
- Puedes sacrificar 5-8% de precisión por **2-3x más velocidad**
- Necesitas **menor consumo de memoria**
- Trabajas principalmente con textos cortos

### 📈 **Upgrade a BAAI/bge-base-en-v1.5** si:
- Necesitas **mejor precisión** y puedes pagar el costo
- Tienes recursos suficientes (3x más memoria)
- La precisión es más importante que la velocidad
- Quieres mantener la misma familia BGE

### 🌍 **Cambiar a BAAI/bge-m3** si:
- Necesitas **soporte multilingüe** (100+ idiomas)
- Trabajas con **documentos largos** (hasta 8192 tokens)
- Tienes recursos abundantes
- Necesitas funcionalidad avanzada

---

## Tabla Comparativa Resumida

| Modelo | Dimensiones | Parámetros | Velocidad | Precisión | Mejor para |
|--------|-------------|------------|-----------|-----------|------------|
| **bge-small-en-v1.5** ⭐ | 384 | 33.4M | Media | Alta | Balance óptimo |
| all-MiniLM-L6-v2 | 384 | 22M | **Muy alta** | Media | Velocidad |
| all-mpnet-base-v2 | 768 | 110M | Baja | Media-Alta | General |
| bge-base-en-v1.5 | 768 | 109M | Baja | **Muy alta** | Precisión |
| e5-large-v2 | 1024 | 335M | Muy baja | Muy alta | Precisión máxima |
| bge-m3 | 1024 | 567M | Muy baja | Muy alta | Multilingüe |

---

## Conclusión

El modelo actual **BAAI/bge-small-en-v1.5** es una **excelente elección** que ofrece:
- ✅ Estado del arte en su categoría de tamaño
- ✅ Balance óptimo entre velocidad y precisión
- ✅ Tamaño razonable (33.4M parámetros)
- ✅ Rendimiento superior a alternativas populares como all-MiniLM-L6-v2 y all-mpnet-base-v2

### Opciones más potentes:
1. **BAAI/bge-base-en-v1.5** - Mejor precisión, 3x más pesado
2. **intfloat/e5-large-v2** - Aún mejor precisión, 10x más pesado
3. **BAAI/bge-m3** - Máxima versatilidad, 17x más pesado

### Opción más rápida (pero menos precisa):
- **sentence-transformers/all-MiniLM-L6-v2** - 2-3x más rápido, 5-8% menos preciso

**Recomendación final**: Mantener el modelo actual a menos que tengas necesidades específicas de velocidad extrema o precisión máxima.
