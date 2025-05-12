import click
import getpass
from pwgen import pwgen

from app.commands.email import send_adduser_email, send_reset_email
from ..extentions.database import mongo
from werkzeug.security import generate_password_hash
from flask import Blueprint
import os

SENDMAIL = os.environ.get('SENDMAIL', 'FALSE').upper()
if SENDMAIL == "TRUE":
    SENDMAIL = True
else:
    SENDMAIL = False

userCommands = Blueprint('user',__name__)

# db.users {
#   "username": "email@dmain.com",
#   "tipo": "vip|temp|admin|teste|free|paid"
#    "active": True,
#    "passwordActive": False
#    "lastLogin": timestamp
#    "lastPaid": timestamp
#    "excludeOn": timestamp
# }

@userCommands.cli.command("getUser")
@click.argument("username")
def get_user(username):
    userCollection = mongo.db.users.find_one({"username": username})
    print(userCollection)

@userCommands.cli.command("listUsers")
def list_users():
    lista_users = [u for u in mongo.db.users.find()]
    ativos = ""
    inativos = ""
    #print(lista_users)
    for u in lista_users:
        if u["active"]:
            ativos += " " + u["username"]
        else:
            inativos += " " + u["username"]
    print(f'Lista de users active ativos:{ativos}')
    print(f'Lista de users active inativos:{inativos}')

@userCommands.cli.command("setUser")
@click.argument("user")
@click.argument("tipo")
@click.argument("status")
def list_users(user,tipo,status):
    if status == "true":
        status = True
    elif status == "false":
        status = False
    userCollection = mongo.db.users
    userExists = userCollection.find_one({"username": user})
    if userExists:
        userCollection.find_one_and_update({'username': user},{'$set': {tipo: status}})
        print("Usuário",user,"setado para status",tipo,"=",status)
    else:
        print("Usuário não encontrado.")

@userCommands.cli.command("dropUser")
@click.argument("username")
def delete_user(username):
    userCollection = mongo.db.users
    userExists = userCollection.find_one({"username": username})
    if userExists:
        question = input(f'Deseja deletar o usuário {username}? (S/N) ')
        if question.upper() == "S":
            userCollection.delete_one({"username": username})
            print("Usuário deletado com sucesso!")
        else:
            exit()
    else:
        print("Usuário não encontrado.")
