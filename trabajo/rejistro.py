from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import bcrypt
import smtplib
from email.mime.text import MIMEText

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def inicio():
    return {"mensaje": "Servidor funcionando"}

# Configuración de la conexión a MySQL
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
        print("Error al conectar a la base de datos:", e)
        return None

# Modelos para request
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

class SolicitudCertificado(BaseModel):
    usuario_id: int
    universidad: str
    facultad: str
    fecha_inicio: str
    fecha_fin: str
    correo: str
    archivo_titulo: str

# Función para enviar correo
def enviar_correo(destinatario, asunto, mensaje):
    remitente = "ana"
    password = "analia1930"
    msg = MIMEText(mensaje)
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = destinatario

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
    except Exception as e:
        print("Error enviando correo:", e)

@app.post("/registro")
def registrar_usuario(datos: UsuarioRegistro):
    print("📩 Registro recibido:", datos.dict())  # 👈 Mostrar en consola
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (datos.usuario,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    hashed_password = bcrypt.hashpw(datos.password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)",
                   (datos.usuario, hashed_password.decode('utf-8')))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Usuario registrado correctamente"}

@app.post("/login")
def login_usuario(datos: UsuarioLogin):
    print("🔐 Intento de login:", datos.dict())  # 👈 Mostrar en consola
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (datos.usuario,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    if usuario is None:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    if not bcrypt.checkpw(datos.password.encode('utf-8'), usuario['password'].encode('utf-8')): # type: ignore
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    return {"mensaje": f"Bienvenido, {usuario['usuario']}", "usuario_id": usuario['id']} # type: ignore

@app.post("/solicitud/acta")
def solicitar_acta(datos: SolicitudActa):
    print("📝 Solicitud de Acta:", datos.dict())  # 👈 Mostrar en consola
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO solicitud_acta_nacimiento
        (usuario_id, nombre, apellido, cedula, fecha_nacimiento, correo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (datos.usuario_id, datos.nombre, datos.apellido, datos.cedula, datos.fecha_nacimiento, datos.correo))
    conn.commit()
    cursor.close()
    conn.close()
    enviar_correo(datos.correo, "Solicitud de Acta de Nacimiento", "Tu solicitud fue recibida correctamente.")
    return {"mensaje": "Solicitud de acta enviada y correo enviado"}

@app.post("/solicitud/certificado")
def solicitar_certificado(datos: SolicitudCertificado):
    print("📚 Solicitud de Certificado:", datos.dict())  # 👈 Mostrar en consola
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO solicitud_certificado_estudios
        (usuario_id, universidad, facultad, fecha_inicio, fecha_fin, correo, archivo_titulo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (datos.usuario_id, datos.universidad, datos.facultad, datos.fecha_inicio, datos.fecha_fin, datos.correo, datos.archivo_titulo))
    conn.commit()
    cursor.close()
    conn.close()
    enviar_correo(datos.correo, "Solicitud de Certificado de Estudios", "Tu solicitud fue recibida correctamente.")
    return {"mensaje": "Solicitud de certificado enviada y correo enviado"}


#C:\Users\luzan\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --reload
