import json
from flask import Blueprint, current_app, make_response, redirect, render_template, session, request, url_for, flash
from ..extentions.database import mongo
from ..cache import cache
from app.variables import *
from app.data.maincontent import *

site = Blueprint('site',__name__)

#current_app.logger.debug info warning error

def getLang():
    cooklang = request.cookies.get("preflang")
    if cooklang is not None:
        current_app.logger.debug(f'Getting preferred language {cooklang} from cookie')
        if cooklang not in SUPPORTED_LANGS:
            cooklang = 'en'
    else:
        # Check preferred language
        preferred_languages = request.accept_languages
        cooklang = preferred_languages.best_match(SUPPORTED_LANGS)
        current_app.logger.debug(f'Getting preferred language {cooklang} from request')
        if cooklang is None:
            current_app.logger.debug('Setting default preferred lang en')
            cooklang = 'en'
    return cooklang

# def basicdata(menu,lang):
#     if lang in SUPPORTED_LANGS:
#         return {
#             'menuitem': MENUITEM,
#             'menu': menu,
#             'lang': lang
#         }
#     else:
#         flash(f'Language {lang} not valid','danger')
#         return redirect(url_for('site.home'))

def gera_menudata(menu):
    menudata = MENUITEM
    menudata['active'] = menu
    menudata["lang"] = getLang()
    return menudata

@site.route('/set_language/<lang>')
def set_language(lang):
    if lang in SUPPORTED_LANGS:
        response = make_response(redirect(request.referrer or '/'))
        response.set_cookie('preflang', lang)
        return response
    else:
        return redirect('/')


@site.route('/')
def home():
    resp = make_response(render_template("home.html",menudata=gera_menudata("home")))
    #resp.set_cookie('preflang',cook)
    return resp

# @site.route('/<lang>')
# def homelang(lang):
#     return render_template("home.html",bdata=basicdata('Home',lang))

@cache.cached(timeout=3600)
@site.route('/about')
def contact():
    return render_template("about.html",menudata=gera_menudata('about'),content=ABOUT)
