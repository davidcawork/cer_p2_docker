#!/usr/bin/env python3

from flask import Flask, render_template, redirect, request, session
from src.webscraper import WebScraper
from src.beebotteclient import BeebotteClient
from src.elasticlient import ElastiClient
import threading, time, re, requests, uuid, logging, hashlib

# Iniciamos los objs necesarios de Flask, Elasticsearch y Beebotte
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

elastic = ElastiClient('172.26.0.2', 9200)
beebot = BeebotteClient('qCZWxhok0QX7B8jM0AJ9KooM', 'cWRCglPqI6lUsMkkzMBk6tYdgt2cinR7')

# Vars globales
media_1 = 0.0
media_2 = 0.0


# Thread A: Flask Operations
@app.route("/")
def index():
    """
        Página principal de la app
    """
    if 'email' in session:
        # Obtenemos el ID del user 
        _id = elastic.getIDByMail(session['email'])

        return render_template('index_sup.html', random_num = WebScraper.getRandomNumber(),  msg = session['user'] + ' is already online!', media1= str(media_1), media2= str(media_2), pet_1 = str(elastic.getPets(_id)[0]), pet_2=str(elastic.getPets(_id)[1]))
 
    return render_template('index.html', random_num = WebScraper.getRandomNumber())

@app.route("/register")
def register():
    """
        Página de registro de la app
    """
    if 'email' in session:
        session.clear()
    return render_template('register.html')


@app.route("/success", methods = ['POST'])
def success():
    """
        Página de registro exitoso de la app
    """
  
    session['email'] = request.form['email']
    session['user'] = request.form['name']
    session['pass'] = request.form['pass']
    session['peticiones'] = 0

    # Va mos a comprobar si el user o el mail ya existen 
    if elastic.getNumberOfUsersByEmail(session['email']) == 0 and  elastic.getNumberOfUsersByName(session['user']) == 0:
        
        # Vamos añadir al user a la base datos
        salt = uuid.uuid4().hex
        key = hashlib.sha256(salt.encode() + session['pass'].encode()).hexdigest() + ':' + salt

        elastic.storeUser({"username": session['user'], "mail": session['email'],"password": key, "peticiones_media1":0, "peticiones_media2":0})

        logging.debug('Ususario ' + session['user']+ 'registrado en la web!')
    else:
        return render_template('register.html', msg = 'Usuario registrado anteriormente, inicie sesion')

    return render_template('success.html', usr = session['user'])

@app.route("/exit")
def logout():
    """
        Página de salida de la app
    """
    if 'email' in session:
        session.clear()
    return render_template('exit.html')

@app.route("/login")
def login():
    """
        Página de entrada de la app
    """
    if 'email' in session:
        # Obtenemos el ID del user 
        _id = elastic.getIDByMail(session['email'])

        return render_template('index_sup.html', random_num = WebScraper.getRandomNumber(),  msg = session['user'] + ' is already online!', media1= str(media_1), media2= str(media_2), pet_1 = str(elastic.getPets(_id)[0]), pet_2=str(elastic.getPets(_id)[1]))
    else:
        return render_template('login.html')

@app.route("/successlogin", methods = ['POST'])
def successlogin():
    """
        Página de entrada a la app
    """
    mail = request.form['email']
    passw = request.form['pass']

    if elastic.getNumberOfUsersByEmail(mail) != 0:
        # Obtenemos el ID del user 
        _id = elastic.getIDByMail(mail)

        # Obtenemos la info del user
        user_data = elastic.getUserByID(_id)

        # Obtenemos la sal y la pass hasheada
        passw_user, salt = user_data['_source']['password'].split(':')

        # Calculamos el hash de la contraseña introducida
        passw_intro = hashlib.sha256(salt.encode() + passw.encode()).hexdigest()  

        if passw_intro == passw_user:
            logging.debug('Autenticación del usuario '+user_data['_source']['username']+' realizada con exito!')
            session['user'] = user_data['_source']['username']
            session['email'] = user_data['_source']['mail']
            session['password'] = user_data['_source']['password']
            session['peticiones_media1'] = user_data['_source']['peticiones_media1']
            session['peticiones_media2'] = user_data['_source']['peticiones_media2']
            
            return render_template('index_sup.html', random_num = WebScraper.getRandomNumber(),  msg = session['user'] + ' is already online!', media1= str(media_1), media2= str(media_2), pet_1 = str(elastic.getPets(_id)[0]), pet_2=str(elastic.getPets(_id)[1]))
    
        else:
            return render_template('login.html', msg = "Contraseña incorrecta :(")
    else:
        return render_template('login.html', msg = "Correo no registrado en la app")


@app.route("/media1", methods = ['GET'])
def media1():
    """
        Página de entrada de la app CON MEDIA LOCAL
    """
    global media_1

    if 'email' in session:
        # Obtenemos la el mail de la cookie de la session
        mail = session['email']

        # Obtenemos el ID del user 
        _id = elastic.getIDByMail(mail)

        # Actualizamos el numero de peticiones 
        elastic.updatePetsLocal(_id, 1)

        # Pedimos la media nueva
        media_1 = elastic.getMean()

        return render_template('index_sup.html', random_num = WebScraper.getRandomNumber(),  msg = session['user'] + ' is already online!', media1= str(media_1), media2= str(media_2), pet_1 = str(elastic.getPets(_id)[0]), pet_2=str(elastic.getPets(_id)[1]))
    else:
        return render_template('index.html', random_num = WebScraper.getRandomNumber())

@app.route("/media2", methods = ['GET'])
def media2():
    """
        Página de entrada de la app CON MEDIA EXTERNA
    """
    global media_2

    if 'email' in session:
        # Obtenemos la el mail de la cookie de la session
        mail = session['email']

        # Obtenemos el ID del user 
        _id = elastic.getIDByMail(mail)

        # Actualizamos el numero de peticiones 
        elastic.updatePetsExterna(_id, 1)

        # Pedimos la media nueva
        media_2 = beebot.getMean()

        return render_template('index_sup.html', random_num = WebScraper.getRandomNumber(),  msg = session['user'] + ' is already online!', media1= str(media_1), media2= str(media_2), pet_1 = str(elastic.getPets(_id)[0]), pet_2=str(elastic.getPets(_id)[1]))
    else:
        return render_template('index.html', random_num = WebScraper.getRandomNumber())


@app.route("/umbral", methods = ['POST'])
def umbral():
    """
        Página de UMBRAL
    """
    umbral = request.form['umbral']

    # Obtenemos el umbral
    umbral_list = elastic.getUmbral(umbral)

    number = [data['_source']['number'] for data in umbral_list ]

    return render_template('umbral.html', umbral = str(number))


# Thread B: Get  periodic data
def thread_getData():
    while True:
        
        # Primero solocitamos un nuevo numero
        random_num = WebScraper.getRandomNumber()

        # Loggeamos que numero vamosa meter en ambas bases de datos
        logging.debug('Se va almacenar el numero: '+ str(random_num))

        # Guardamos en la base de datos local
        elastic.storeNumber(random_num)

        # Guardamos en la base de datos externa
        beebot.storeNumber(float(random_num))

        # Esperamos 2 mins
        time.sleep(120)

# Main of our app
if __name__ == '__main__':
    
    # Ponemos el nivel de log deseado 
    logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    
    #Seleep
    time.sleep(10)
    
    # Nos aseguramos que Elasticsearch y beebotte estan OK!
    elastic.checkElasticsearch(True)
    beebot.checkBeebotte()
    
    # Let's initialize the threads
    t = threading.Thread(target=thread_getData, daemon=True)
    t.start()

    # Then, we have to start out flask app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

