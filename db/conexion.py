# db/conexion.py
import psycopg2

def obtener_conexion():
    return psycopg2.connect(
        host="hashing-bd.cw94q8sgiyyo.us-east-1.rds.amazonaws.com",
        dbname="postgres",
        user="grupo2",
        password="grupo2_123"
    )
