#!/usr/bin/env python3
"""
Script de reparación CRÍTICO para Location UUID → VARCHAR.
Ejecuta ANTES de migrate usando SQL directo sin Django.
"""
import os
import sys

def fix_location_uuid_to_varchar():
    """Convierte Location.id de UUID a VARCHAR(32) usando psycopg2 directo."""
    try:
        import psycopg2
        from urllib.parse import urlparse
    except ImportError as e:
        print(f"❌ Error importando dependencias: {e}")
        return False
    
    # Obtener DATABASE_URL desde variables de entorno
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL no configurada, asumiendo BD no existe aún")
        return True
    
    print(f"🔧 Conectando a base de datos...")
    
    try:
        # Parsear DATABASE_URL
        parsed = urlparse(database_url)
        
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],  # Quitar el / inicial
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Conexión establecida")
        
        # Verificar si la tabla core_location existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'core_location'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("✅ Tabla core_location no existe aún, skip conversion")
            cursor.close()
            conn.close()
            return True
        
        # Verificar tipo de columna id
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'core_location' 
            AND column_name = 'id'
        """)
        
        result = cursor.fetchone()
        if not result:
            print("⚠️  Columna core_location.id no existe aún")
            cursor.close()
            conn.close()
            return True
        
        data_type = result[0]
        print(f"📊 Tipo actual de core_location.id: {data_type}")
        
        if data_type != 'uuid':
            print(f"✅ core_location.id ya es {data_type}, no requiere conversión")
            cursor.close()
            conn.close()
            return True
        
        print("🔧 Iniciando conversión UUID → VARCHAR(32)...")
        
        # PASO 1: Obtener todas las FKs que apuntan a core_location.id
        cursor.execute("""
            SELECT 
                tc.table_name, 
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'core_location'
            AND ccu.column_name = 'id'
        """)
        
        fks = cursor.fetchall()
        print(f"📋 Encontradas {len(fks)} foreign keys")
        
        # PASO 2: Eliminar FKs
        for table_name, constraint_name, column_name in fks:
            print(f"   🗑️  Eliminando FK: {table_name}.{constraint_name}")
            cursor.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}')
        
        # PASO 3: Convertir core_location.id de UUID a VARCHAR(32)
        print("   🔄 Convirtiendo core_location.id: UUID → VARCHAR(32)")
        cursor.execute("""
            ALTER TABLE core_location 
            ALTER COLUMN id TYPE VARCHAR(32) 
            USING REPLACE(id::text, '-', '')
        """)
        
        # PASO 4: Convertir columnas FK
        for table_name, constraint_name, column_name in fks:
            print(f"   🔄 Convirtiendo {table_name}.{column_name}")
            cursor.execute(f"""
                ALTER TABLE {table_name} 
                ALTER COLUMN {column_name} TYPE VARCHAR(32)
                USING CASE 
                    WHEN {column_name} IS NULL THEN NULL
                    ELSE REPLACE({column_name}::text, '-', '')
                END
            """)
        
        # PASO 5: Recrear FKs
        print("   🔗 Recreando foreign keys...")
        for table_name, constraint_name, column_name in fks:
            new_constraint_name = f"{table_name}_{column_name}_fkey"
            cursor.execute(f"""
                ALTER TABLE {table_name} 
                ADD CONSTRAINT {new_constraint_name} 
                FOREIGN KEY ({column_name}) 
                REFERENCES core_location(id) 
                DEFERRABLE INITIALLY DEFERRED
            """)
            print(f"   ✅ Recreada FK: {table_name}.{column_name}")
        
        cursor.close()
        conn.close()
        
        print("✅ Conversión completada exitosamente")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("🔧 FIX CRÍTICO: Location UUID → VARCHAR Conversion")
    print("=" * 70)
    
    success = fix_location_uuid_to_varchar()
    
    if success:
        print("\n✅ Script completado exitosamente")
        sys.exit(0)
    else:
        print("\n⚠️  Script completado con warnings/errores")
        print("   Continuando con migrate (puede fallar si UUID aún existe)")
        sys.exit(0)  # No fallar el build, dejar que migrate intente
