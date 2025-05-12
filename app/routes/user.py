from datetime import datetime
from flask import Blueprint, current_app, jsonify, render_template, session, request, url_for, flash
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer

from ..cache import cache
from app.routes.site import gera_menudata, getLang
from ..extentions.database import mongo
from app.variables import *
from app.data.maincontent import *
from app.commands.email import send_email
from datetime import date, datetime, timedelta
import jwt

usermod = Blueprint('usermod',__name__)

@cache.cached(timeout=180)
def get_user_info(username):
    userCollection = mongo.db.users.find_one({"username": username})
    return userCollection

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def send_confirmation_email(username):
    user = mongo.db.users.find_one({"username": username})
    if not user:
        return False

    lang=getLang()
    SUBJECT = {
        'en': "User created",
        'pt': "Usuário criado"
    }

    token = user['email_confirmation_token']
    confirm_url = url_for('usermod.confirm_email', token=token, _external=True)

    TEXTO = {
        'en': "Your user were created. Click the link below to confirm your email.",
        'pt': "Seu usuário foi criado. Clique no link abaixo para confirmar seu email."
    }
    corpo_html=f"""
    <h1 style=\"text-align: center\">Portal leafarlins - {SUBJECT[lang]}</h1>
    <p>{TEXTO[lang]}</p>
    <a href="{confirm_url}">{confirm_url}</a>"""
    corpo_text = f"{SUBJECT[lang]} - {TEXTO[lang]}"
    corpo_text+=f"{confirm_url}"

    BODY_HTML = """<html>
    <head></head>
    <body style=\"font-family: \"Trebuchet MS\", Arial, Helvetica, sans-serif;\">
    """ + corpo_html + """
    </body>
    </html>
                """
    BODY_TEXT = (corpo_text)

    return send_email(username,SUBJECT[lang],BODY_TEXT,BODY_HTML)

@usermod.route('/confirm/<token>')
def confirm_email(token):
    try:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=86400  # Expires in 24 hours
        )
    except:
        return "Invalid or expired token", 400

    # Update user in MongoDB
    result = mongo.db.users.update_one(
        {"username": email},
        {"$set": {"active": True, "email_confirmed": True}}
    )

    if result.modified_count == 1:
        flash(f'User activated','success')
    else:
        flash(f'User not found','danger')
    return redirect(url_for("usermod.login"))

@usermod.route('/api/check_user_validity', methods=['GET'])
def check_user_validity():
    # Extract authentication information (e.g., session cookie)
    if "username" in session:
        u_info = get_user_info(session["username"])
        return jsonify({'logedin': True,
                        'username': session["username"],
                        'active': u_info['active'],
                        'tipo': u_info.get('tipo')})
    else:
        return jsonify({'logedin': False})

@usermod.route('/login', methods=['GET','POST'])
def login():
    next_url = request.args.get('next')
    current_app.logger.debug(f"Next url link: {next_url}")
    lang = getLang()
    if "username" in session:
        if next_url:
            return redirect(next_url)
        return redirect(url_for('site.home'))
    elif request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
        userFound = mongo.db.users.find_one({"username": username})
        next_url = request.form.get('next')
        FLASH = {
            "welcome" : {
                "en" : "Welcome",
                "pt" : "Bem vindo"
            },
            "logfail" : {
                "en" : "Login failed",
                "pt" : "Erro no login"
            },
            "unotactive" : {
                "en" : "User not active, contact page owner",
                "pt" : "Usuário inativo, contate administrador"
            },
            "checkemail" : {
                "en" : "Check email to activate user",
                "pt" : "Verifique seu e-mail para ativar o usuário"
            }
        }
        if userFound:
            validUser = userFound["username"]
            validPassword = userFound["password"]
            validActiveU = userFound["active"]
            validEmailC = userFound["email_confirmed"]

            if validActiveU:
                if check_password_hash(validPassword,password):
                    session["username"] = validUser
                    session["tipo"] = userFound["tipo"]
                    current_app.logger.info(f"User {validUser} logged in")
                    mongo.db.users.update_one(
                        {"username": username},
                        {"$set": {"last_login": datetime.utcnow()}})

                    # JWT token for others
                    token = jwt.encode(
                        {
                            "sub": username,
                            "tip": userFound["tipo"],
                            "exp": datetime.utcnow() + timedelta(hours=24)  # Expires in 24h
                        },
                        current_app.config['SECRET_KEY'],  # Use your Flask secret key
                        algorithm="HS256"
                    )
                    if next_url:
                        current_app.logger.debug(f"Login done, next url link: {next_url}")
                        return redirect(f"{next_url}#token={token}")
                    else:
                        flash(f'{FLASH["welcome"][lang]}, {validUser}','success')
                        return redirect(url_for('site.home'))
                else:
                    flash(f"{FLASH["logfail"][lang]}","danger")
                    current_app.logger.info(f"User {validUser} login failed with wrong password")
            else:
                if validEmailC:
                    flash(f'{FLASH["unotactive"][lang]}','warning')
                    current_app.logger.info(f"User {validUser} not active, login failed")
                else:
                    flash(f"{FLASH["checkemail"][lang]}",'warning')
                    current_app.logger.info(f"User {validUser} email not confirmed")
        else:
            flash(f"{FLASH["logfail"][lang]}","danger")
            current_app.logger.warn(f"User {username} not found in database",'danger')

    return render_template("usuarios/login.html",menudata=gera_menudata("login"),content=LOGIN,lang=lang)

# db.users {
#   "username": "email@dmain.com",
#   "tipo": "vip|temp|admin|teste|free|paid"
#    "active": True,
#    "confirmation_token" : "xxxxx"
#    "email_confirmed" : True
#    "lastLogin": timestamp
#    "lastPaid": timestamp
#    "excludeOn": timestamp
# }

@usermod.route('/createuser', methods=['GET','POST'])
def createuser():
    if request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
        password2 = request.form.get('senha2')
        userFound = mongo.db.users.find_one({"username": username})
        userExists = mongo.db.users.find_one({"username": username})
        if userExists:
            current_app.logger.info(f"Error creating user {username}: already exists")
            flash("User exists","danger")
        elif (password != password2):
            flash('Passwords do not match','danger')
        elif len(password) < 6:
            flash('Passwords must have size > 5','warning')
        else:
            user = {
                "username": username,
                "password": generate_password_hash(password),
                "tipo" : "free",
                "active": False,
                "email_confirmation_token": generate_confirmation_token(username),
                "email_confirmed": False,
                "last_login": None,
                "created_at": datetime.utcnow()
            }
            try:
                outdb = mongo.db.users.insert_one(user)
            except Exception as e:
                current_app.logger.error(f"Error creating user {username}: {e}")
                flash('Error creating user','danger')
            if outdb:
                current_app.logger.info(f"User {username} created")
                flash(f'Success creating user','success')
                output_email = send_confirmation_email(username)
                if output_email:
                    current_app.logger.info(f"Confirmation email successfuly send to {username}")
                else:
                    current_app.logger.error(f"Error sending confirmation email to {username}")
                    flash(f'Error sending confirmation to email','warning')

        return redirect(url_for("usermod.login"))
    else:
        if "username" in session:
            return redirect(url_for('site.home'))
        else:
            return render_template("usuarios/create.html",menudata=gera_menudata("login"))

# Main app route (/api/check-auth)
@usermod.route('/api/check-auth')
def check_auth():
    current_app.logger.debug(f"Got username to validate")
    if "username" in session:
        token = jwt.encode(
            {"sub": session["username"], "tip": session["tipo"], "exp": datetime.utcnow() + timedelta(hours=1)},
            current_app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        return jsonify({"logged_in": True, "token": token})
    else:
        return jsonify({"logged_in": False}), 401

@usermod.route('/reset', methods=['GET','POST'])
def reset():
    if request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
        password2 = request.form.get('senha2')
        userFound = mongo.db.users.find_one({"username": username})
        if userFound:
            validUser = userFound["username"]
            validActive = userFound["active"]
            if validActive:
                if (password == password2):
                    mongo.db.users.find_one_and_update(
                        {"username": username},
                        {'$set': {"password": generate_password_hash(password)}})
                    # Current site session
                    session["username"] = validUser
                    flash(f'Success, welcome {validUser}','success')
                    return redirect(url_for('site.home'))
                else:
                    flash('Passwords do not match','danger')
            else:
                flash('User not active, contact page owner','warning')
                current_app.logger.info(f"User {validUser} not active, login failed")

        else:
            flash("User not found",'danger')

    return redirect(url_for("usermod.login"))

# @usermod.route('/validate-token', methods=['POST'])
# def validate_token():
#     token = request.json.get('token')
#     current_app.logger.debug(f"Got token to validate: {token}")
#     try:
#         decoded = jwt.decode(
#             token,
#             current_app.config['SECRET_KEY'],
#             algorithms=["HS256"]
#         )
#         # Optional: Verify the user still exists in DB
#         user = mongo.db.users.find_one({"username": decoded["sub"]})
#         if user:
#             return jsonify({"valid": True, "username": decoded["sub"]})
#         else:
#             return jsonify({"valid": False}), 401
#     except jwt.ExpiredSignatureError:
#         return jsonify({"valid": False, "error": "Token expired"}), 401
#     except jwt.InvalidTokenError:
#         return jsonify({"valid": False, "error": "Invalid token"}), 401

@usermod.route('/logout')
def logout():
    session.pop("username",None)
    session.pop("tipo",None)
    flash('Logout finished')
    return redirect(url_for('usermod.login'))

@usermod.route('/privacy')
def privacy():

    return render_template('usuarios/privacy.html',menudata=gera_menudata("login"),lang=getLang())
