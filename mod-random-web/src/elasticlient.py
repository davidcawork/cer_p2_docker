#!/usr/bin/python3

from elasticsearch import Elasticsearch
import os, logging, requests, uuid, time

class ElastiClient(object):
    """
        Clase para gestionar la base de datos
    """
    def __init__(self, host = 'localhost', port = 9200, usr_table = 'users', num_table = 'numbers'):
        """
            Constructor de la clase
        """
        self.host = host
        self.port = port
        self.usr_table = usr_table
        self.num_table = num_table
        self.es = Elasticsearch([{'host': self.host, 'port': self.port}])
        
    def checkElasticsearch(self, isContainer):
        """
            Método para asegurarse que el servicio está corriendo
        """

        if not isContainer:
            # Si el servicio esta inactivo lo levantamos
            if os.system('systemctl is-active --quiet elasticsearch.service') != 0:
                logging.debug('Servicio elasticsearch.service inactivo... levantando')
                os.system('systemctl start elasticsearch.service')
            else:
                logging.debug('Servicio elasticsearch.service activo!')

        # Comprobamos que Elasticsearch esté corriendo en el puerto y en el host indicado
        if requests.get('http://' + self.host + ':' + str(self.port)).text is not None:
            logging.debug('Elasticsearch corriendo correctamente en ' + self.host + ':' + str(self.port))
        else:
            logging.error('No se ha encontrado el servicio de Elasticsearch corriendo en ' + self.host + ':' + str(self.port))
    
        # Nos aseguramos que los index estan bien
        self.initDataTables()


    def initDataTables(self):
        """
            Metodo para iniciar correctamente las tablas que se van a utilizar
        """

        
        settings = {
            "numbers": {
                "properties": {
                    "number": {
                        "type": "float"
                    }
                }
            }
        }        

        # Vamos a empezar por la tabla de numeros rng
        if self.es.indices.exists(index=self.num_table):
            logging.debug('Se ha encontrado index ' + self.num_table +' creado... regenerando')
            
            # Primero eliminamos
            self.es.indices.delete(index=self.num_table)

            # Despues regeneramos la tabla 
            self.es.indices.create(index= self.num_table, ignore=400, mappings = settings)

        else:
            # Si no existe la creamos y ya
            logging.debug('Generando index ' + self.num_table + ' ...')
            self.es.indices.create(index= self.num_table, ignore=400, mappings = settings)


        # Ahora vamos a ver si existe la base de datos del ususario 
        if self.es.indices.exists(index=self.usr_table):
            logging.debug('Se ha encontrado index ' + self.usr_table +' creado... regenerando')

            # Primero eliminamos
            self.es.indices.delete(index=self.usr_table)

            # Despues regeneramos la tabla
            self.es.indices.create(index= self.usr_table)
        
        else:
            # Si no existe la creamos y ya
            logging.debug('Generando index ' + self.usr_table + ' ...')
            self.es.indices.create(index= self.usr_table)
            
            
    def storeNumber(self, data):
        """
            Metodo para añadir datos a la base de datos
        """
        self.es.index(index = self.num_table, id = uuid.uuid4().int, document= {'number': float(data)})        


    def getMean(self):
        """
            Metodo para obtener la media de la base de datos
        """
        return round(self.es.search(index= self.num_table, aggs= {'avg_number':{'avg':{ 'field': 'number'}}})['aggregations']['avg_number']['value'], 2)

        

    def getNumberByID(self, _id):
        """
            Metodo para conseguir un numero de la base de datos por ID
        """
        return self.es.get(index =  self.num_table, id = _id)
        

    def storeUser(self, _usr):
        """
            Metodo para añadir un usuario a la base de datos 
        """
        self.es.index(index = self.usr_table, id = uuid.uuid4().int, document = _usr)


    def getNumberOfUsersByEmail(self, email):
        """
            Metodo para obtener el numero de ususarios con un email dado
        """
        return self.es.search(index = self.usr_table, query = {'match_phrase': { 'mail': email}})['hits']['total']['value']


    def getNumberOfUsersByName(self, name):
        """
            Metodo para obtener el numero de ususarios con un nombre dado
        """
        return self.es.search(index = self.usr_table, query = {'match': { 'username': name}})['hits']['total']['value']


    def getIDByUsername(self, name):
        """
            Metodo para obtener el ID asociado a un usuario por su nombre
        """
        return self.es.search(index = self.usr_table, query = {'match': { 'username': name}})['hits']['hits'][0]['_id']

    

    def getIDByMail(self, mail):
        """
            Metodo para obtener el ID asociado a un usuario por su mail
        """
        return self.es.search(index = self.usr_table, query = {'match': { 'mail': mail}})['hits']['hits'][0]['_id']


    def getUserByID(self, _id):
        """
            Obtenemos un usuario por ID
        """
        return self.es.get(index = self.usr_table, id = _id)


    def updatePetsLocal(self, _id, _pet):
        """
            Metodo para actualziar las peticiones de un ususario BBDD LOCAL
        """
        
        # Primero sacamos la info del user 
        usr_data = self.getUserByID(_id)
        
        # Hacemos el update delos datos
        new_usr_data = usr_data['_source']
        new_usr_data['peticiones_media1'] = new_usr_data['peticiones_media1'] + _pet

        # Actualizamos al ususario
        self.es.index(index = self.usr_table, id = _id, document = new_usr_data)

    
    def updatePetsExterna(self, _id, _pet):
        """
            Metodo para actualziar las peticiones de un ususario BBDD EXTERNA
        """
        
        # Primero sacamos la info del user 
        usr_data = self.getUserByID(_id)
        
        # Hacemos el update delos datos
        new_usr_data = usr_data['_source']
        new_usr_data['peticiones_media2'] = new_usr_data['peticiones_media2'] + _pet

        # Actualizamos al ususario
        self.es.index(index = self.usr_table, id = _id, document = new_usr_data)


    def getPets(self, _id):
        """
            Metodo para obtener las peticiones de los usuarios
        """
        # Primero sacamos la info del user 
        usr_data = self.getUserByID(_id)

        return [ usr_data['_source']['peticiones_media1'], usr_data['_source']['peticiones_media2'] ]
    

    def getUmbral(self, umbral):
        """
            Metodo para obtener umbral
        """
        # Primero sacamos la info del user 
        data = self.es.search(index= self.num_table, query= {"range" : { 'number': { 'gt' : float(umbral)}}})

        return data['hits']['hits']


    def getSearch(self, _index):
        """
            Metodo para realizar una busqueda en la base de datos por index 
        """
        return self.es.search(index= _index)

