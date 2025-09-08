# Import libraries
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv
import psycopg
import psycopg.rows
from io import BytesIO
import pandas as pd
import smtplib
import secrets
import re
import os

load_dotenv()

# New instance Flask
app = Flask(__name__)


app.config["SECRET_KEY"] = secrets.token_hex(16)

# Secure connection using environment variables
cnx = psycopg.connect(
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT"),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD")
)

# Define routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add_data", methods=['POST'])
def add_data():
    form_data = {
        'identificador_laboratorio': request.form.get('identificador_laboratorio'),
        'nombre_docente': request.form.get('nombre_docente'),
        'correo_electronico': request.form.get('correo_electronico'),
        'programa': request.form.get('programa'),
        'hora_ingreso': request.form.get('hora_ingreso'),
        'hora_salida': request.form.get('hora_salida'),
        'observacion': request.form.get('observacion')
    }
    try:
        # Get form data
        fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Form fields validation empty
        if not all(form_data.values()):
            flash("Todos los campos son obligatorios.", category='warning')
            return render_template('index.html', form_data=form_data)
        if not re.match(r"^[A-Za-z\s]+$", form_data['nombre_docente']):
            flash("El nombre del docente solo puede contener letras y espacios.", category='warning')
            return render_template('index.html', form_data=form_data)
        if not re.match(r"^[^,\s]+@(unicesmag\.edu\.co)$", form_data['correo_electronico']):
            flash("Correo electrónico no válido. Debe ser un correo institucional.", category='warning')
            return render_template('index.html', form_data=form_data)
        if form_data['hora_ingreso'] >= form_data['hora_salida']:
            flash("La hora de salida debe ser después de la hora de ingreso.", category='warning')
            return render_template('index.html', form_data=form_data)
        # Save data to database
        cursor = cnx.cursor()
        query = """
        INSERT INTO control_laboratorios_sistemas (fecha_registro, identificador_laboratorio, nombre_docente, correo_electronico, programa, hora_ingreso, hora_salida, observacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (fecha_registro, *form_data.values()))
        cnx.commit()
        flash("Datos guardados exitosamente.", category='success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error: {e}", category='danger')
        return render_template('index.html', form_data=form_data)
 
@app.route("/login", methods=["GET", "POST"])
def login_admin():
    # Clean session exising
    session.clear() 
    # Check if then from is submitted
    if request.method == "POST": 
        input_username = request.form.get("username") 
        input_password = request.form.get("password") 
        # Validate field input
        if not input_username:
            return render_template("login.html", message=1) 
        elif not input_password:
            return render_template("login.html", message=2) 
        # Create cursor to return dictionary 
        cursor = cnx.cursor(row_factory=psycopg.rows.dict_row)
        cursor.execute('SELECT * FROM users WHERE username = %s', (input_username,))
        user = cursor.fetchone()
        # Validate credencials user
        if user is None or not check_password_hash(user["hashed_password"], input_password):
            return render_template("login.html", message=3)
        session["user_id"] = user["id"] 
        return redirect("/admin") 
    return render_template("login.html")

@app.route("/goback")
@login_required
def goback():
    # Redirect page admin
    return redirect("/admin")

@app.route("/admin")
@login_required
def admin_data():
    cursor = cnx.cursor()
    # Select table database
    cursor.execute('SELECT * FROM control_laboratorios_sistemas ORDER BY fecha_registro DESC')
    data = cursor.fetchall()
    return render_template("/admin.html", data = data)

@app.route("/edit/<id>")
@login_required
def get_data(id):
    # Create cursor database
    cursor = cnx.cursor()
    cursor.execute('SELECT * FROM control_laboratorios_sistemas WHERE id = %s',(id,))
    # Get query result
    data = cursor.fetchall()
    return render_template("edit.html", id = data[0])

def normalize_incidencia(value):
    """
    Normalize the value for comparison:
    - Treat None, empty strings, and the string 'none' (case-insensitive) as equivalent ('').
    """
    if value is None:
        return ''
    value = str(value).strip()
    return '' if value.lower() == 'none' else value

@app.route("/update/<id>", methods=['POST'])
@login_required
def update_data(id):
    if request.method == 'POST':
        # Get updated form data from the request
        fecha_registro = request.form['fecha_registro']
        identificador_laboratorio = request.form['identificador_laboratorio']
        nombre_docente = request.form['nombre_docente']
        correo_electronico = request.form['correo_electronico']
        programa = request.form["programa"]
        hora_ingreso = request.form['hora_ingreso']
        hora_salida = request.form['hora_salida']
        observacion = request.form['observacion']
        respuesta_incidencia = request.form['respuesta_incidencia']
        # Create a new database cursor
        cursor = cnx.cursor()
        # Get the previous value of 'respuesta_incidencia' from the database
        cursor.execute("SELECT respuesta_incidencia FROM control_laboratorios_sistemas WHERE id = %s", (id,))
        resultado = cursor.fetchone()
        respuesta_incidencia_anterior = resultado[0] if resultado else None
        # Prepare the value to be stored in the database (None if empty or only spaces)
        respuesta_incidencia_db = respuesta_incidencia if respuesta_incidencia and str(respuesta_incidencia).strip() else None
        # Update all fields in the database
        query = """
            UPDATE control_laboratorios_sistemas
            SET fecha_registro = %s,
                identificador_laboratorio = %s,
                nombre_docente = %s,
                correo_electronico = %s,
                programa = %s,
                hora_ingreso = %s,
                hora_salida = %s,
                observacion = %s,
                respuesta_incidencia = %s
            WHERE id = %s
        """
        cursor.execute(query, (
            fecha_registro, identificador_laboratorio, nombre_docente, correo_electronico,
            programa, hora_ingreso, hora_salida, observacion, respuesta_incidencia_db, id
        ))
        cnx.commit()
        # Only send email if 'respuesta_incidencias' was actually changed
        if normalize_incidencia(respuesta_incidencia_anterior) != normalize_incidencia(respuesta_incidencia_db):
            # Send notification email to the user
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            email_user = os.environ.get("EMAIL_USER")
            email_pass = os.environ.get("EMAIL_PASS")
            server.login(email_user, email_pass)
            subject = "Control de Laboratorios de Sistemas - Respuesta a su Incidencia"
            body = f"""
Estimado/a usuario/a,


Le informamos que hemos actualizado la respuesta a su incidencia registrada en el sistema de Control de Laboratorios de Sistemas.


**Detalles de la incidencia:** 
{observacion}


**Respuesta a su incidencia:** 
{respuesta_incidencia_db}


Atentamente, 
Equipo de Soporte Técnico 
Universidad CESMAG


(Por favor, no responda a este correo si no requiere atención adicional)
"""
            msg = MIMEText(body, "plain", "utf-8")
            msg["From"] = email_user
            msg["To"] = correo_electronico
            msg["Subject"] = subject
            server.sendmail(email_user, correo_electronico, msg.as_string())
            server.quit()
            flash("Respuesta de incidencia enviada exitosamente.")
        else:
            flash('Datos actualizados exitosamente.')
        return redirect(url_for('admin_data'))
        
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = cnx.cursor()
    # Delete data form
    cursor.execute('DELETE FROM control_laboratorios_sistemas WHERE id = {0}'.format(id))
    cnx.commit()
    flash("Datos eliminados correctamente.")
    return redirect(url_for('admin_data'))

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        # Get data user
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")
        # Validate data user
        if not input_username:
            return render_template("register.html", message=1)
        elif not input_password:
            return render_template("register.html", message=2)
        elif not input_confirmation:
            return render_template("register.html", message=4)
        elif input_password != input_confirmation:
            return render_template("register.html", message=3)
        # Check if the username already exists
        cursor = cnx.cursor(row_factory=psycopg.rows.dict_row)
        cursor.execute('SELECT * FROM users WHERE username = %s', (input_username,))
        if cursor.fetchone():
            return render_template("register.html", message=5)
        # Generate hashed password
        hash_password = generate_password_hash(input_password, method='pbkdf2:sha256', salt_length=8)
        cursor.execute('INSERT INTO users (username, hashed_password) VALUES (%s, %s) RETURNING id', (input_username, hash_password))
        result = cursor.fetchone()
        new_user_id = result['id'] if result and 'id' in result else None
        cnx.commit()
        # Saving id user
        session["user_id"] = new_user_id
        flash(f"Usuario registrado como {input_username}")
        return redirect("/admin")
    return render_template("register.html")

@app.route("/users")
@login_required
def users():
    cursor = cnx.cursor()
    # Select table users
    cursor.execute('SELECT * FROM users')
    data = cursor.fetchall()
    return render_template("/users.html", data=data)

@app.route("/restore/<id>", methods=['GET', 'POST'])
@login_required
def restore(id):
    cursor = cnx.cursor()
    # Get form restore
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        # Initialize message variable
        message_code = 0
        # Get the current username from the database to keep it unchanged
        cursor.execute("SELECT username FROM users WHERE id = %s", (id,))
        user = cursor.fetchone()
        current_username = user[0] if user else ''
        # Validate passwords
        if not new_password:
            message_code = 2  # Password is empty
        elif new_password != confirmation:
            message_code = 3  # Passwords do not match
        else:
            # Generate hash for new password
            hash_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
            cursor.execute("UPDATE users SET hashed_password = %s WHERE id = %s", (hash_password, id))
        # Commit changes only if there are no validation errors
        if message_code == 0:
            cnx.commit()
            flash("Datos actualizados exitosamente.")
            return redirect("/users")
        # Render template with appropriate message and current username
        return render_template("restore.html", message=message_code, id=id, username=current_username)
    # Get data user form
    cursor.execute("SELECT username FROM users WHERE id = %s", (id,))
    user = cursor.fetchone()
    username = user[0] if user else ''
    return render_template("restore.html", message=0, id=id, username=username)

@app.route("/deleteuser/<id>")
@login_required
def deleteuser(id):
    cursor = cnx.cursor()
    # Detele user database
    cursor.execute('DELETE FROM users WHERE id = %s', (id,))
    cnx.commit()
    flash("Usuario eliminado correctamente.")
    return redirect("/users")

@app.route("/reports", methods=['GET'])
@login_required
def reports():
    # Render template reports
    return render_template("/reports.html")

@app.route("/generate", methods=['GET', 'POST'])
@login_required
def generate():
    # Create a database cursor
    cursor = cnx.cursor()
    # Check if the request method is POST
    if request.method == 'POST':
        # Retrieve start and end dates from the form
        start_end = request.form['start_date'] + " 00:00:00"
        end_date = request.form['end_date'] + " 23:59:59"
        print("start_end", start_end)
        print("end_date", end_date)
        # Store the selected dates in the session for later use
        session['start_date'] = start_end
        session['end_date'] = end_date
        # Execute a SQL query to select records within the specified date range
        cursor.execute(
            'SELECT * FROM control_laboratorios_sistemas WHERE fecha_registro BETWEEN %s AND %s', 
            (start_end, end_date)
        )
    else:
        # If the request method is GET, retrieve all records from the table
        cursor.execute('SELECT * FROM control_laboratorios_sistemas')
    # Fetch all results from the executed query
    data = cursor.fetchall()
    # Render the generate.html template and pass the fetched data to it
    print(data)
    return render_template("/generate.html", data=data)

@app.route("/download")
@login_required
def download():
    # Retrieve the dates stored in the session
    start_date = session.get('start_date')
    end_date = session.get('end_date')
    # Create database cursor and fetch data
    with cnx.cursor() as cursor:
        query = (
            "SELECT * FROM control_laboratorios_sistemas "
            "WHERE fecha_registro BETWEEN %s AND %s" if start_date and end_date 
            else "SELECT * FROM control_laboratorios_sistemas"
        )
        cursor.execute(query, (start_date, end_date) if start_date and end_date else ())
        data = cursor.fetchall()
        # Remove the ID column
        data = [row[1:] for row in data]
    # Define column names for the Excel file
    columns = [
        'Fecha', 'Laboratorio', 'Nombres',
        'Correo electrónico', 'Programa',
        'Hora de ingreso', 'Hora de salida',
        'Observaciones', 'Respuesta'
    ]
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    # Format date column
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
    # Ensure that the time columns are treated as strings directly from the database
    df['Hora de ingreso'] = df['Hora de ingreso'].astype(str).str.strip()
    df['Hora de salida'] = df['Hora de salida'].astype(str).str.strip()
    # Remove any unwanted prefixes (like "0 days") by slicing the string if necessary
    df['Hora de ingreso'] = df['Hora de ingreso'].str.replace(r'^\d+ days ', '', regex=True)
    df['Hora de salida'] = df['Hora de salida'].str.replace(r'^\d+ days ', '', regex=True)
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Reporte', index=False)
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Reporte']
        # Add formats for header row
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter'
        })
        # Format the header row
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)
        # Adjust column widths dynamically
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2  # Add some padding
            worksheet.set_column(idx, idx, max_length)
    # Reset pointer to the beginning of the BytesIO stream
    output.seek(0)
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'reporte_control_laboratorios_sistemas_{timestamp}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
    
@app.route("/logout")
@login_required
def logout():
    # Clean session
    session.clear() 
    return redirect("/")

# Start server
if __name__ == "__main__":
    app.run(debug=True)