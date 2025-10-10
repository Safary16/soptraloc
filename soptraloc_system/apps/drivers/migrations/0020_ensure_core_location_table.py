# Generated manually - Asegura que core_location existe
# CRÍTICO: En DB desde cero, ninguna migración crea la tabla core_location
# porque:
# - drivers.0003 crea drivers_location (ya no aplica, replaced)
# - drivers.0011/0013 solo RENOMBRAN si existe
# - drivers.0014 solo cambia metadata (SeparateDatabaseAndState)
#
# Esta migración CREA la tabla si no existe (idempotente)

from django.db import migrations


def create_core_location_if_not_exists(apps, schema_editor):
    """
    Crea la tabla core_location si no existe.
    Idempotente: seguro ejecutar múltiples veces.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Verificar si core_location existe
        if db_vendor == 'postgresql':
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'core_location'
                );
            """)
        else:  # SQLite
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='core_location';
            """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ core_location ya existe, omitiendo creación")
            return
        
        print("🔧 Creando tabla core_location...")
        
        # Crear tabla con estructura actual de drivers.Location
        if db_vendor == 'postgresql':
            cursor.execute("""
                CREATE TABLE core_location (
                    id VARCHAR(32) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    code VARCHAR(20) NOT NULL UNIQUE,
                    address TEXT DEFAULT '',
                    latitude NUMERIC(10, 8) NULL,
                    longitude NUMERIC(11, 8) NULL,
                    city VARCHAR(100) DEFAULT '',
                    region VARCHAR(100) DEFAULT '',
                    country VARCHAR(100) DEFAULT 'Chile',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:  # SQLite
            cursor.execute("""
                CREATE TABLE core_location (
                    id VARCHAR(32) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    code VARCHAR(20) NOT NULL UNIQUE,
                    address TEXT DEFAULT '',
                    latitude DECIMAL(10, 8) NULL,
                    longitude DECIMAL(11, 8) NULL,
                    city VARCHAR(100) DEFAULT '',
                    region VARCHAR(100) DEFAULT '',
                    country VARCHAR(100) DEFAULT 'Chile',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        print("✅ Tabla core_location creada exitosamente")


class Migration(migrations.Migration):

    dependencies = [
        ("drivers", "0019_alter_location_options"),
    ]

    operations = [
        migrations.RunPython(
            create_core_location_if_not_exists,
            reverse_code=migrations.RunPython.noop
        ),
    ]
