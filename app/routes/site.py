import json
from flask import Blueprint, current_app, make_response, render_template, session, request, url_for, flash
import pymongo
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash
from pwgen import pwgen
from app.routes.backend import get_text, get_user_flashcards, set_to_known, set_to_study, get_flashcard, update_fc
from ..extentions.database import mongo
from ..cache import cache
from data.variables import *

site = Blueprint('site',__name__)

#app.logger.debug('This is a DEBUG message')
#app.logger.info('This is an INFO message')
#app.logger.warning('This is a WARNING message')
#app.logger.error('This is an ERROR message')

def basicdata(menu,lang):
    if lang in SUPPORTED_LANGS:
        return {
            'menuitem': MENUITEM,
            'menu': menu,
            'lang': lang
        }
    else:
        flash(f'Language {lang} not valid','danger')
        return redirect(url_for('site.home'))

@site.route('/')
def home():
    cook = request.cookies.get("preflang")
    if cook not in SUPPORTED_LANGS:
        cook = 'en'
    resp = make_response(render_template("home.html",bdata=basicdata('Home',cook)))
    resp.set_cookie('preflang',cook)
    return resp

@site.route('/<lang>')
def homelang(lang):
    return render_template("home.html",bdata=basicdata('Home',lang))

@cache.cached(timeout=3600)
@site.route('/<lang>/about')
def about(lang):
    return render_template("about.html",bdata=basicdata('About',lang))