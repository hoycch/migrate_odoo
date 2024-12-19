import psycopg2

# Database connection details
connection = psycopg2.connect(
    host="192.168.50.224",
    database="odoo",
    user="odoo",
    password="odoo",
    port=8001
)

try:
    with connection.cursor() as cursor:
        # Get a list of all tables in the public schema
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema='public';
        """)
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            
            # Get the columns for each table
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}'")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            if column_names:
                # Construct a search query for each table
                search_query = f"""
                    SELECT * FROM {table_name} WHERE 
                    CONCAT_WS(' ', {', '.join(column_names)}) ILIKE '%http://192.168.50.224:8000%';
                """
                cursor.execute(search_query)
                results = cursor.fetchall()
                
                if results:
                    print(f"Table: {table_name}")
                    for result in results:
                        print(result)

finally:
    connection.close()
