#!/usr/bin/env python
"""
Script de reparación pre-migrate para Render.
Ejecutar ANTES de python manage.py migrate
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.db import connection

def fix_location_uuid_to_varchar():
    """Convierte Location.id de UUID a VARCHAR(32) si es necesario."""
    with connection.cursor() as cursor:
        # Verificar si la tabla existe y si id es UUID
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'core_location' 
            AND column_name = 'id'
        """)
        
        result = cursor.fetchone()
        if not result:
            print("✅ Tabla core_location no existe aún, skip")
            return
        
        data_type = result[0]
        if data_type != 'uuid':
            print(f"✅ core_location.id ya es {data_type}, skip")
            return
        
        print("🔧 Convirtiendo core_location.id de UUID a VARCHAR(32)...")
        
        # Eliminar TODAS las FKs que apuntan a core_location.id
        cursor.execute("""
            SELECT tc.table_name, tc.constraint_name
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
        print(f"   Eliminando {len(fks)} foreign keys...")
        for table_name, constraint_name in fks:
            cursor.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}')
            print(f"   ✓ Eliminada FK: {table_name}.{constraint_name}")
        
        # Convertir UUID a VARCHAR(32) sin guiones
        print("   Convirtiendo Location.id de UUID a VARCHAR...")
        cursor.execute("""
            ALTER TABLE core_location 
            ALTER COLUMN id TYPE VARCHAR(32) 
            USING REPLACE(id::text, '-', '')
        """)
        
        # Convertir todas las columnas FK también
        tables_fks = [
            ('containers_container', 'current_location_id'),
            ('containers_container', 'terminal_id'),
            ('containers_containermovement', 'from_location_id'),
            ('containers_containermovement', 'to_location_id'),
            ('warehouses_warehouse', 'location_id'),
            ('routing_locationpair', 'origin_id'),
            ('routing_locationpair', 'destination_id'),
            ('routing_actualoperationrecord', 'location_id'),
            ('routing_actualtriprecord', 'location_id'),
            ('drivers_traveltime', 'from_location_id'),
            ('drivers_traveltime', 'to_location_id'),
        ]
        
        for table, column in tables_fks:
            # Verificar si la tabla y columna existen
            cursor.execute(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, [table, column])
            
            if cursor.fetchone():
                print(f"   Convirtiendo {table}.{column}...")
                cursor.execute(f"""
                    ALTER TABLE {table} 
                    ALTER COLUMN {column} TYPE VARCHAR(32)
                    USING CASE 
                        WHEN {column} IS NULL THEN NULL
                        ELSE REPLACE({column}::text, '-', '')
                    END
                """)
                print(f"   ✓ Convertido {table}.{column}")
        
        # Recrear las FKs
        print("   Recreando foreign keys...")
        fk_definitions = {
            ('containers_container', 'current_location_id'): 'containers_container_current_location_fk',
            ('containers_container', 'terminal_id'): 'containers_container_terminal_fk',
            ('containers_containermovement', 'from_location_id'): 'containers_containermovement_from_location_fk',
            ('containers_containermovement', 'to_location_id'): 'containers_containermovement_to_location_fk',
            ('warehouses_warehouse', 'location_id'): 'warehouses_warehouse_location_fk',
            ('routing_locationpair', 'origin_id'): 'routing_locationpair_origin_fk',
            ('routing_locationpair', 'destination_id'): 'routing_locationpair_destination_fk',
            ('routing_actualoperationrecord', 'location_id'): 'routing_actualoperationrecord_location_fk',
            ('routing_actualtriprecord', 'location_id'): 'routing_actualtriprecord_location_fk',
            ('drivers_traveltime', 'from_location_id'): 'drivers_traveltime_from_location_fk',
            ('drivers_traveltime', 'to_location_id'): 'drivers_traveltime_to_location_fk',
        }
        
        for (table, column), constraint_name in fk_definitions.items():
            # Verificar si existe la tabla
            cursor.execute(f"""
                SELECT 1 FROM information_schema.tables WHERE table_name = %s
            """, [table])
            
            if cursor.fetchone():
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ADD CONSTRAINT {constraint_name} 
                        FOREIGN KEY ({column}) 
                        REFERENCES core_location(id) 
                        DEFERRABLE INITIALLY DEFERRED
                    """)
                    print(f"   ✓ Recreada FK: {table}.{column}")
                except Exception as e:
                    print(f"   ⚠️  No se pudo recrear FK {table}.{column}: {e}")
        
        print("✅ Conversión completada exitosamente")

if __name__ == '__main__':
    try:
        fix_location_uuid_to_varchar()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
