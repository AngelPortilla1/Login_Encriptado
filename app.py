from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from cryptography.fernet import Fernet
import os
from datetime import date
import jwt
from datetime import datetime, timedelta

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


from dotenv import load_dotenv
load_dotenv()



JWT_SECRET = os.getenv("JWT_SECRET")

# Clave para encriptación nivel 2 (simétrica)
# Mejor práctica: guardar en un archivo o variable de entorno
FERNET_KEY_FILE = "fernet_key.key"

# Intenta cargar la clave existente o crea una nueva
if os.path.exists(FERNET_KEY_FILE):
    with open(FERNET_KEY_FILE, "rb") as key_file:
        FERNET_KEY = key_file.read()
else:
    FERNET_KEY = Fernet.generate_key()
    with open(FERNET_KEY_FILE, "wb") as key_file:
        key_file.write(FERNET_KEY)

fernet = Fernet(FERNET_KEY)

# Configuración Flask
app = Flask(__name__)
CORS(app)

# Función para obtener conexión a la base de datos
def get_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="grupo2",
        password="grupo2_123",
        host="hashing-bd.cw94q8sgiyyo.us-east-1.rds.amazonaws.com",
        cursor_factory=RealDictCursor
    )

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    nick_name = data.get("nick_name")  # Consistente con el nombre en JavaScript
    contrasena = data.get("contrasena")  # Consistente con el nombre en JavaScript
    
    if not nick_name or not contrasena:
        return jsonify({"success": False, "message": "Campos incompletos."})
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id_usuario, u.nick_name, d.contrasena, d.email
                FROM usuarios u
                JOIN detalle_usuarios d ON u.id_usuario = d.id_usuario
                WHERE u.nick_name = %s
            """, (nick_name,))
            user = cur.fetchone()
            
            if not user:
                return jsonify({"success": False, "message": "Usuario no encontrado."})
            
            try:
                stored_password = fernet.decrypt(user['contrasena'].encode()).decode()
            except Exception:
                return jsonify({"success": False, "message": "Error al desencriptar la contraseña."})
            
            if stored_password == contrasena:
                    # Genera token JWT válido por 1 minuto
                payload = {
                    "user_id": user["id_usuario"],
                    "nick_name": user["nick_name"],
                    "exp": datetime.utcnow() + timedelta(minutes=60)
                }
                token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
                return jsonify({
                    "success": True,
                    "message": "Login exitoso.",
                    "email": user["email"],
                    "token": token # En producción deberías generar un token JWT real
                })
            else:
                return jsonify({"success": False, "message": "Contraseña incorrecta."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error de servidor: {str(e)}"})
    finally:
        if conn:
            conn.close()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    nick_name = data.get("nick_name")  # Cambiado a nick_name para ser consistente
    contrasena = data.get("contrasena")  # Cambiado a contrasena para ser consistente
    email = data.get("email")
    
    if not nick_name or not contrasena or not email:
        return jsonify({"success": False, "message": "Campos incompletos."})
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Verifica si el nickname ya existe
            cur.execute("SELECT * FROM usuarios WHERE nick_name = %s", (nick_name,))
            if cur.fetchone():
                return jsonify({"success": False, "message": "El usuario ya existe."})
            
            # 1. Insertar en usuarios
            cur.execute(
                "INSERT INTO usuarios (nick_name, fecha) VALUES (%s, %s) RETURNING id_usuario",
                (nick_name, date.today())
            )
            id_usuario = cur.fetchone()['id_usuario']
            
            # 2. Insertar en detalles_usuario
            encrypted_password = fernet.encrypt(contrasena.encode()).decode()
            cur.execute(
                """INSERT INTO detalle_usuarios
        (id_usuario, contrasena, token, grupo, email, estado_cuenta)
        VALUES (%s, %s, %s, %s, %s, %s)""",
    (id_usuario, encrypted_password, "default_token", 2, email, True)
            )
            conn.commit()
            
            return jsonify({"success": True, "message": "Usuario registrado exitosamente."})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": f"Error de servidor: {str(e)}"})
    finally:
        if conn:
            conn.close()
@app.route("/perfil", methods=["GET"])
def perfil():
    # Obtener el token del encabezado Authorization
    auth_header = request.headers.get("Authorization")
    print("Auth header recibido:", auth_header)  # Debug
    
    # Verificar si el token está presente y tiene el prefijo "Bearer "
    if not auth_header or not auth_header.startswith("Bearer "):
        print("Token inválido o faltante")  # Debug
        return jsonify({"success": False, "message": "Token de autorización inválido."}), 401
    
    # Obtener solo el token
    token = auth_header.split(" ")[1]
    print("Token extraído:", token)  # Debug

    try:
        # Decodificar el token JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("Payload decodificado:", payload)  # Debug
        user_id = payload.get("user_id")

        # Obtener los datos del usuario desde la base de datos
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(""" 
                SELECT u.nick_name, d.email 
                FROM usuarios u 
                JOIN detalle_usuarios d ON u.id_usuario = d.id_usuario 
                WHERE u.id_usuario = %s
            """, (user_id,))
            usuario = cur.fetchone()

        if usuario:
            return jsonify({"success": True, "usuario": usuario})
        else:
            return jsonify({"success": False, "message": "Usuario no encontrado."}), 404

    except ExpiredSignatureError:
        return jsonify({"success": False, "message": "El token ha expirado."}), 401
    except InvalidTokenError:
        return jsonify({"success": False, "message": "Token inválido."}), 401
    except Exception as e:
        return jsonify({"success": False, "message": f"Error de servidor: {str(e)}"}), 500


if __name__ == "__main__":
    print(f"🔐 Clave Fernet utilizada: {FERNET_KEY.decode()}")
    app.run(debug=True)