from flask import request, jsonify, render_template
from urllib import urlencode
from model import insert_sound, get_sound_by_id
from model import store_captcha, save_sound
import requests

translate_base_url = 'http://translate.google.com/translate_tts'

captcha_base_url = 'http://ipv6.google.com/sorry/CaptchaRedirect'

continue_url = 'http://translate.google.com/translate_tts?ie=UTF-8&q=words&tl=en&q=what'

s = requests.Session()

def create():
    lang = request.form['lang']
    text = request.form['text']

    # TODO: Bypass Google Translate if sound already exists in DB

    params = build_translate_url_params(lang, text)
    translate_url = translate_base_url + '?' + params

    r = s.get(translate_url)

    if r.status_code == 503:
        captcha = store_captcha(s, r.text)
        template = render_template('captcha.html', captcha=captcha, lang=lang,
                                   text=text)
        res = build_create_failure_response(template)
    elif r.status_code == 200:
        sound_path = save_sound(lang, text, r.content)
        idd = insert_sound(lang, text, sound_path)
        res = { 'success': True, 'id': idd }
    else:
        # TODO: Implement
        pass

    return jsonify(**res)

def get_sound(idd):
    sound = get_sound_by_id(idd)
    # TODO change from shorthand lang to full word(s)
    lang = sound[1]
    text = sound[2]
    path = '/' + sound[3]
    return render_template('sound.html', lang=lang, text=text, path=path)

def receive_captcha():
    idd = request.form['id']
    captcha = request.form['captcha']
    lang = request.form['lang']
    text = request.form['text']

    params = build_captcha_url_params(idd, captcha)
    captcha_url = captcha_base_url + '?' + params

    r = s.get(captcha_url)

    if r.status_code == 503:
        captcha = store_captcha(s, r.text)
        template = render_template('captcha.html', captcha=captcha, lang=lang,
                                   text=text)
        res = build_create_failure_response(template)
    elif r.status_code == 200:
        res = build_captcha_success_response(lang, text)
    else:
        # TODO return 500 or something
        pass

    return jsonify(**res)

def build_create_failure_response(template):
    return {
        'success': False,
        'template': template
    }

def build_captcha_success_response(lang, text):
    return {
        'success': True,
        'lang': lang,
        'text': text
    }

def build_translate_url_params(lang, text):
    return urlencode({
        'ie': 'UTF-8',
        'tl': lang,
        'q' : text
    })

def build_captcha_url_params(idd, captcha):
    return urlencode({
        'continue': continue_url,
        'id': idd,
        'captcha': captcha,
        'submit': 'Submit'
    })
