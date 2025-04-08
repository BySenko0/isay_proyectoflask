from flask import Flask, render_template, request, redirect, session, url_for, flash
import requests
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
API_BASE_URL = "http://127.0.0.1:8000"
app.secret_key = os.urandom(24)  # Esto genera una clave secreta aleatoria

# ------------ Rutas Públicas ------------

@app.route('/')
def index():
    return render_template('/dashboard.html')

@app.route('/comics')
def comic():
    return render_template('/comiclista.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        payload = {
            "correo": email,
            "password": password
        }

        try:
            # Usamos el endpoint correcto de FastAPI
            response = requests.post(f"{API_BASE_URL}/cliente/login", json=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            flash(f"Error al iniciar sesión: {http_err}", "danger")
            return redirect(url_for("login"))
        except Exception as err:
            flash(f"Ocurrió un error: {err}", "danger")
            return redirect(url_for("login"))

        user_data = response.json()
        session["user"] = user_data
        flash("Bienvenido/a de nuevo", "success")

        # Redirigir según el rol
        if user_data.get("rol") == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("dashboard"))

    return render_template("auth/login.html")



# Ruta de registro actualizada para GET y POST
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Obtener datos del formulario
        name = request.form.get("name")
        email = request.form.get("email")
        role = request.form.get("role")
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")

        # Validar que las contraseñas coincidan
        if password != password_confirmation:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("register"))

        # ✅ Aquí está el payload con los nombres que espera FastAPI
        payload = {
            "Nombre": name,
            "Correo": email,
            "Ubicacion": "desconocido",
            "Rol": role,
            "Estado": "activo",
            "Cooldown": "0",
            "url_perfil": "default.jpg",
            "contrasena": password
        }

        try:
            response = requests.post(f"{API_BASE_URL}/usuarios", json=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            flash(f"Error en el registro (HTTP): {http_err}", "danger")
            return redirect(url_for("register"))
        except Exception as err:
            flash(f"Error en el registro: {err}", "danger")
            return redirect(url_for("register"))

        flash("Usuario registrado exitosamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html")

@app.route('/logout')
def auth_logout():
    session.clear()  # Limpiar la sesión
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))

# ------------ Rutas de usuario (requieren autenticación) ------------

@app.route('/dashboard')
def dashboard():
    return render_template('user/dashboard.html')



@app.route('/comunidad')
def comunidad():
    return render_template('user/comunidad.html')

@app.route('/comentarios')
def comentarios():
    return render_template('user/comentarios.html')

@app.route('/perfil')
def perfil():
    return render_template('user/perfil.html')

@app.route('/configuracion')
def configuracion():
    return render_template('user/configuracion.html')

# ------------ Rutas de administración ------------

@app.route('/admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/comics')
def admin_comics():
    try:
        response = requests.get(f"{API_BASE_URL}/comics")
        response.raise_for_status()
        comics = response.json()
    except Exception as e:
        flash(f"Error al cargar cómics: {e}", "danger")
        comics = []

    return render_template('admin/comics.html', comics=comics)




@app.route('/admin/usuarios')
def admin_users():
    try:
        response = requests.get(f"{API_BASE_URL}/usuarios")
        response.raise_for_status()
        usuarios = response.json()
    except Exception as e:
        flash(f"Error al cargar usuarios: {e}", "danger")
        usuarios = []

    return render_template('admin/dashboard_users.html', usuarios=usuarios)

@app.route('/admin/comics/crear', methods=["GET", "POST"])
def crear_comic_admin():
    if request.method == "POST":
        try:
            # Recoger campos del formulario
            data = {
                "nombre": request.form.get("nombre"),
                "autor": request.form.get("autor"),
                "descripcion": request.form.get("descripcion"),
                "categoria": request.form.get("categoria"),
                "stock": request.form.get("stock"),
                "precio": request.form.get("precio"),
                "proveedor_id": request.form.get("proveedor_id"),
                "editorial": request.form.get("editorial"),
                "formato": request.form.get("formato"),
                "idioma": request.form.get("idioma"),
                "precio_oferta": request.form.get("precio_oferta") or request.form.get("precio"),
                "costo_proveedor": request.form.get("costo_proveedor") or 0,
                "fecha_lanzamiento": request.form.get("fecha_lanzamiento") or ""
            }

            imagen = request.files.get("imagen")
            if not imagen:
                flash("Debes subir una imagen", "danger")
                return redirect(url_for("crear_comic_admin"))

            files = {
                "imagen": (imagen.filename, imagen.read(), imagen.mimetype)
            }

            response = requests.post(f"{API_BASE_URL}/comics", data=data, files=files)
            response.raise_for_status()

            flash("Cómic creado exitosamente", "success")
            return redirect(url_for("admin_comics"))

        except Exception as e:
            flash(f"Error al crear cómic: {e}", "danger")
            return redirect(url_for("crear_comic_admin"))

    # GET: mostrar formulario
    try:
        res = requests.get(f"{API_BASE_URL}/proveedores")
        res.raise_for_status()
        proveedores = res.json()
    except Exception as e:
        flash(f"Error al cargar proveedores: {e}", "danger")
        proveedores = []

    return render_template("admin/agregarcomic.html", proveedores=proveedores)


@app.route('/admin/usuarios/editar/<int:id>', methods=["GET", "POST"])
def editar_usuario(id):
    if request.method == "POST":
        data = {
            "Nombre": request.form.get("nombre"),
            "Ubicacion": request.form.get("ubicacion"),
            "Rol": request.form.get("rol"),
            "Estado": request.form.get("estado"),
            "Cooldown": request.form.get("cooldown"),
            "url_perfil": request.form.get("url_perfil"),
        }

        try:
            response = requests.put(f"{API_BASE_URL}/usuarios/{id}", json=data)
            response.raise_for_status()
            flash("Usuario actualizado correctamente", "success")
        except Exception as e:
            flash(f"Error al actualizar usuario: {e}", "danger")

        return redirect(url_for("admin_users"))

    try:
        response = requests.get(f"{API_BASE_URL}/usuarios/{id}")
        response.raise_for_status()
        usuario = response.json()
    except Exception as e:
        flash(f"No se pudo cargar el usuario: {e}", "danger")
        return redirect(url_for("admin_users"))

    return render_template("admin/form_usuario.html", usuario=usuario, modo="editar")

@app.route('/admin/usuarios/eliminar/<int:id>', methods=["POST"])
def eliminar_usuario(id):
    try:
        response = requests.post(f"{API_BASE_URL}/usuarios/{id}/delete")  # <-- este endpoint acepta POST
        response.raise_for_status()
        flash("Usuario eliminado correctamente", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el usuario: {e}", "danger")

    return redirect(url_for("admin_users"))






@app.route('/admin/empresas')
def admin_companies():
    try:
        response = requests.get("http://127.0.0.1:8000/proveedores")
        response.raise_for_status()
        proveedores = response.json()
    except Exception as e:
        flash(f"Error al cargar proveedores: {e}", "danger")
        proveedores = []

    return render_template('admin/provedores.html', proveedores=proveedores)


@app.route('/admin/proveedores/crear', methods=["GET", "POST"])
def admin_crearcompanies():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        telefono = request.form.get("telefono")

        payload = {
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono
        }

        try:
            response = requests.post("http://127.0.0.1:8000/proveedores", json=payload)
            response.raise_for_status()
            flash("Proveedor agregado correctamente", "success")
        except Exception as e:
            flash(f"Error al agregar proveedor: {e}", "danger")

        return redirect(url_for("admin_companies"))

    return render_template("admin/agregarprovedores.html")

@app.route("/admin/proveedores/editar/<int:id>", methods=["GET", "POST"])
def editar_proveedor(id):
    if request.method == "POST":
        data = {
            "nombre": request.form.get("nombre"),
            "correo": request.form.get("correo"),
            "telefono": request.form.get("telefono"),
        }
        try:
            response = requests.put(f"{API_BASE_URL}/proveedores/{id}", json=data)
            response.raise_for_status()
            flash("Proveedor actualizado correctamente", "success")
        except Exception as e:
            flash(f"Error al actualizar proveedor: {e}", "danger")
        return redirect(url_for("admin_companies"))

    try:
        response = requests.get(f"{API_BASE_URL}/proveedores/{id}")
        response.raise_for_status()
        proveedor = response.json()
    except Exception as e:
        flash(f"Error al cargar proveedor: {e}", "danger")
        return redirect(url_for("admin_companies"))

    return render_template("admin/editarproveedor.html", proveedor=proveedor)

@app.route("/admin/proveedores/eliminar/<int:id>", methods=["POST"])
def eliminar_proveedor(id):
    try:
        response = requests.delete(f"{API_BASE_URL}/proveedores/{id}")
        response.raise_for_status()
        flash("Proveedor eliminado correctamente", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el proveedor: {e}", "danger")

    return redirect(url_for("admin_companies"))




@app.route('/admin/puntos-recoleccion')
def admin_pickup_points():
    return render_template('admin/dashboard_pickup_points.html')

@app.route('/admin/comunidad')
def admin_community():
    return render_template('admin/dashboard_community.html')

@app.route('/admin/notificaciones')
def admin_notifications():
    return render_template('admin/dashboard_notifications.html')

@app.route('/admin/ayuda')
def admin_help():
    return render_template('admin/dashboard_help.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
