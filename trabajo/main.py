from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import shutil
import os

app = FastAPI()

# Permitir solicitudes desde el frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, cámbialo a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def inicio():
    return {"mensaje": "Servidor funcionando correctamente"}

# Conexión a MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ana',
            password='analia1930',
            database='docutrack'
        )
        return connection
    except Error as e:
        print("❌ Error al conectar a la base de datos:", e)
        return None

# Modelos
class UsuarioLogin(BaseModel):
    usuario: str
    password: str

class UsuarioRegistro(BaseModel):
    usuario: str
    password: str

class SolicitudActa(BaseModel):
    usuario_id: int
    nombre: str
    apellido: str
    cedula: str
    fecha_nacimiento: str
    correo: str

# Registro de usuario
@app.post("/registro")
def registrar_usuario(datos: UsuarioRegistro):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (datos.usuario,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    import bcrypt
    hashed = bcrypt.hashpw(datos.password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (datos.usuario, hashed.decode('utf-8')))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Usuario registrado correctamente"}

# Login
@app.post("/login")
def login_usuario(datos: UsuarioLogin):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Conexión fallida")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (datos.usuario,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    import bcrypt
    if usuario is None or not bcrypt.checkpw(datos.password.encode(), usuario['password'].encode()):  # type: ignore
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    return {"mensaje": f"Bienvenido {usuario['usuario']}", "usuario_id": usuario['id']}  # type: ignore

# Solicitud de acta de nacimiento
@app.post("/solicitud/acta")
def solicitar_acta(datos: SolicitudActa):
    print("\n" + "="*50)
    print("📄 SOLICITUD DE ACTA DE NACIMIENTO")
    print("="*50)
    print(f"🧑 Usuario ID     : {datos.usuario_id}")
    print(f"📛 Nombre         : {datos.nombre} {datos.apellido}")
    print(f"🪪 Cédula         : {datos.cedula}")
    print(f"🎂 Fecha Nac.     : {datos.fecha_nacimiento}")
    print(f"📧 Correo         : {datos.correo}")
    print("="*50 + "\n")

    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO solicitud_acta_nacimiento 
        (usuario_id, nombre, apellido, cedula, fecha_nacimiento, correo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (datos.usuario_id, datos.nombre, datos.apellido, datos.cedula, datos.fecha_nacimiento, datos.correo))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Solicitud de acta registrada"}

# Solicitud de certificado de estudios
@app.post("/solicitud/certificado")
async def solicitud_certificado(
    usuario_id: int = Form(...),
    universidad: str = Form(...),
    facultad: str = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    correo: str = Form(...)
):
    # Imprimir en consola de forma clara
    print("==============================================")
    print("🎓 SOLICITUD DE CERTIFICADO DE ESTUDIOS")
    print("==============================================")
    print(f"🧑 Usuario ID     : {usuario_id}")
    print(f"🏫 Universidad    : {universidad}")
    print(f"🏢 Facultad       : {facultad}")
    print(f"📅 Fecha Inicio   : {fecha_inicio}")
    print(f"📅 Fecha Fin      : {fecha_fin}")
    print(f"📧 Correo         : {correo}")
    print("==============================================")

    # Insertar en la base de datos
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO solicitud_certificado_estudios 
            (usuario_id, universidad, facultad, fecha_inicio, fecha_fin, correo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (usuario_id, universidad, facultad, fecha_inicio, fecha_fin, correo))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Error al insertar en la base de datos:", e)
        raise HTTPException(status_code=500, detail="Error guardando en la base de datos")
    
    return {"mensaje": "Solicitud de certificado enviada correctamente"}