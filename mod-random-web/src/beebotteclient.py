#!/usr/bin/python3

from beebotte import *
import logging, time

class BeebotteClient(object):
    """
        Clase para gestionar la base de datos externa
    """

    def __init__(self, apiKey, secretKey, host = 'api.beebotte.com', num_table = 'numbers'):
        """
            Constructor de la clase
        """
        self.host = host
        self.apiKey = apiKey
        self.secretKey = secretKey
        self.num_table = num_table
        self.bbt = BBT(self.apiKey, self.secretKey, hostname = self.host)

    def checkBeebotte(self):
        """
            Metodo para comprobar que la base de datos externa esta activa
        """

        # Primero vamosa  comprobar si la API esta online
        if requests.get('http://' + self.host) is not None:
            logging.debug('El host ' + self.host + ' esta activo!')
        else:
            logging.error('No hay conectividad con el host ' + self.host)

        # Vamos a comprobar si el canal ya existe
        try:
            channel = self.bbt.getChannel(self.num_table)
            
            logging.debug('Canal ' + self.num_table + ' encontrado en beebotte... regenerando') 
            
            # Si no falla es por que ya existe ese canal... hay que regenerar
            self.bbt.deleteChannel(self.num_table)
            self.bbt.addChannel(self.num_table,  label = "rngNumbers",  description = "Numeros aleatorios",  ispublic = True,  resources = [{"name": "number", "vtype": BBT_Types.Number }])
        
        except Exception as e: 
            logging.debug('Generando el canal ' + self.num_table + ' ...') 
            self.bbt.addChannel(self.num_table,  label = "rngNumbers",  description = "Numeros aleatorios",  ispublic = True,  resources = [{"name": "number", "vtype": BBT_Types.Number }])
            

    def storeNumber(self, _num):
        """
            Metodo para almacenar un dato
        """
        self.bbt.write(self.num_table, 'number', _num)
        logging.debug('Escribiendo en el canal ' + self.num_table + ' el numero: ' + str(_num))


    def getNumbers(self):
        """
            Metodo para sacar los datos de beebotte
        """
        return self.bbt.read(self.num_table, 'number', limit = 740)
    
    def getMean(self):
        """
            Metodo para obtener la media de la base de datos externa
        """
        data = self.getNumbers()
        mean = 0.0

        # Iteramos sobre la lista
        for number in data:
            mean += number['data']
        
        return mean/len(data)


#logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
#test = BeebotteClient('qCZWxhok0QX7B8jM0AJ9KooM', 'cWRCglPqI6lUsMkkzMBk6tYdgt2cinR7')
#test.checkBeebotte()
#test.storeNumber(1.2)
#time.sleep(1)
#test.storeNumber(2.2)
#time.sleep(1)
#test.storeNumber(62)
#time.sleep(1)
#test.getNumbers()
#print(str(test.getMean()))

