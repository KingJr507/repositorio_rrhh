from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "Annel507/*-+"

# Configuración de la base de datos (Clever Cloud)
db_config = {
    "host": "bd9els7rao1s0zv9rgij-mysql.services.clever-cloud.com",
    "user": "upxgtcjllcmzdmyv",
    "password": "N3a0i2d22FSfvWa1Wiso",
    "database": "bd9els7rao1s0zv9rgij",
    "port": 3306
}

# Carpeta donde se guardarán los PDFs
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(**db_config)

# -------------------- LOGIN ESTUDIANTE --------------------
@app.route("/", methods=["GET", "POST"])
def login_estudiante():
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contrasena"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo_institucional=%s AND contrasena=%s",
                       (correo, contrasena))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            session["usuario"] = usuario["nombre"]
            return redirect("/libros")
        else:
            flash("❌ Usuario o contraseña incorrectos", "danger")

    return render_template("login.html")

@app.route("/libros")
def libros():
    if "usuario" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM libros")
    libros = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("libros.html", libros=libros, usuario=session["usuario"])

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("admin", None)
    return redirect("/")

# -------------------- LOGIN ADMIN --------------------
@app.route("/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE usuario=%s AND contrasena=%s",
                       (usuario, contrasena))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session["admin"] = admin["usuario"]
            return redirect("/panel")
        else:
            flash("❌ Credenciales incorrectas", "danger")

    return render_template("login_admin.html")

# -------------------- PANEL ADMIN --------------------
@app.route("/panel", methods=["GET", "POST"])
def panel():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        titulo = request.form["titulo"]
        autor = request.form["autor"]
        descripcion = request.form["descripcion"]
        archivo = request.files["archivo"]

        if archivo:
            ruta = os.path.join(app.config["UPLOAD_FOLDER"], archivo.filename)
            archivo.save(ruta)
            pdf_path = f"/{ruta}"

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO libros (titulo, autor, descripcion, archivo_pdf) VALUES (%s,%s,%s,%s)",
                           (titulo, autor, descripcion, pdf_path))
            conn.commit()
            cursor.close()
            conn.close()
            flash("✅ Libro agregado con éxito", "success")

    # Obtener todos los libros
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM libros")
    libros = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("panel.html", admin=session["admin"], libros=libros)

# -------------------- ELIMINAR LIBRO --------------------
@app.route("/eliminar_libro/<int:id>", methods=["POST"])
def eliminar_libro(id):
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener ruta del archivo PDF
    cursor.execute("SELECT archivo_pdf FROM libros WHERE id = %s", (id,))
    libro = cursor.fetchone()

    if libro and libro[0]:
        ruta_pdf = libro[0].lstrip("/")  # quitar la barra inicial
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)

    # Eliminar de la base de datos
    cursor.execute("DELETE FROM libros WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("❌ Libro eliminado correctamente", "danger")
    return redirect("/panel")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
