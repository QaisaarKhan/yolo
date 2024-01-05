from FirebaseInterface import Root
from ListenerThreaded import Listener
# from conversion import conversion
import time
import datetime
import threading
import logging
import os
import sys

basepath = os.path.dirname(__file__)
logpath = os.path.abspath(os.path.join(basepath, "LoggingFile.log"))
print("logpath : ", logpath)

formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')



def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    # Arguments:
    #       name : name of logger
    #       log_file : file to append logged data to 
    #       level :   
    # Method:
    #       Function to setup up loggers
    # Output:
    #       None

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger



def startServer():

    # Arguments:
    #       None
    # Method:
    #       Function to start the server
    #           define printing variable, if printing is true then print statements in all functions on server will be executed otherwise they'll not be executed
    #           create logger for logging
    #                   generic logging : to log generic information such as successful execution of threads, exceptions, warnings etc
    #                   labels logging : to log information regarding image, labels generated and the assets selected. This is done for each image
    #           create Listener object
    #           creating the Listener object will start the server
    #       Note:
    #           in a while loop, after every 500 seconds we update a refresh token in the firebase node that is being listened to
    #           this is done to make sure the server never sleeps and to check that the server is still running (in case it is deployed remotely on an AWS machine)
    # Output:
    #       None


    logger = setup_logger('Overall_logger', 'LoggingFile_Generic.log')
    labels_logger= setup_logger('labels-template-user logger', 'LoggingFile_Labels.log')

    # logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', filename= logpath, level=logging.INFO)                  #initialize the logging object
    # logging.info("Create FI Object")

    printing = True

    FI = Root()
    print("Server Started")                                     #server has been started
    obj = Listener(FI, logger, labels_logger, printing)         #Listener object initialized


    refresh_token_bool = True


    while(1):
        time.sleep(500)
        if refresh_token_bool == True:
        	FI.child('FileUrl/refresh_token').update({'refreshToken' : True})
        	refresh_token_bool = False
        else:
        	FI.child('FileUrl/refresh_token').update({'refreshToken' : False})
        	refresh_token_bool = True
        print("PYTHON TOKEN REFRESHED")

startServer()   