import threading
import logging
import datetime
import random
import time

from yolo_class import Yolo


class Listener:
    no_of_processes = 0
    thread_id = 0
    no_of_templates = 2
    
    _LABEL_LIST = 'label'
    _COLOR_LIST = 'color/colors'
    _FILE_URL_NODE = 'FileUrl'
    _EVENT_ID = 'eventId'
    _TEMPLATE_NAME = 'templateName'
    _VISION_NODE = 'CV'
    _URL = 'url'


    _CLASS_TAG = "Listener_YOLO"

    def  __init__(self, FI, logger, labels_logger, printing=False):
        self.printing = printing                                #kept at top because onChange has printing as well and self.printing should be defined before onChange is called in the next line 
        FI.streamListener(self.onChange, self._FILE_URL_NODE)
        self.FI = FI
        self.logger = logger     
        self.labels_logger = labels_logger
        self.YOLO_Model = Yolo(self.printing)
        self.logger.info("Listener initialized with streaming, Firebase and YOLO model")

        print(self._CLASS_TAG + ' - __init__()')


    #MyThread class, nested, this class overrides some thread functions( run) and adds a new function(set_FI)
    class MyThread(threading.Thread):

        _CLASS_TAG = "MyThread"
        _LABEL_LIST_THREAD = 'label'
        _EVENT_ID_THREAD = 'eventId'
        _TEMPLATE_NAME_THREAD = 'templateName'
        _VISION_NODE_THREAD = 'CV'

        def run(self):                                                                      #we ovveride the run function to add try catch around it

            try:
                threading.Thread.run(self)
            except Exception as Argument:
                thread_name = threading.Thread.getName(self)
                # logging.warning("ThreadError: ---" + "Exception raised by Thread ----  " + thread_name) # + " ---- Argument: ", str(Argument))

                self.thread_logger.warning("ThreadError: ---" + "Exception raised by Thread ----  " + thread_name)


                print("Exception raised by ", thread_name)
                print("Argument : ", str(Argument))

                #if exception is raised then update user profile - set AR to default and AR_Updated to true
                splitting = thread_name.split('/',3)                                        #parse thread name using '/'
                user_id = splitting[0]                                                      #the first elemnt is the user_id
                event_id = splitting[1]  
                template_name = splitting[2]                                                #the second elemnt is the event_id
                thread_time = splitting[3]                                                  #the third element is the time

                if self.printing==True:
                    print("user_id: ", user_id)
                    print("event_id: ", event_id)
                    print("template_name: ", template_name)
                    print("time of exception: ", thread_time)

                #Set Default Template
                self.set_default_label(user_id, event_id, template_name)
                # logging.info("Default label added for user {} in event {}".format(user_id,event_id))

                self.thread_logger.info("Default label added in {} for user {} in event {} with template {}".format(self._VISION_NODE_THREAD,user_id,event_id,template_name))

            else:
                thread_name = threading.Thread.getName(self)
                # logging.info("Thread {} has been successfully completed".format(thread_name))

                self.thread_logger.info("Thread {} has been successfully completed".format(thread_name))

        def set_FI(self, thread_FI):

        # Arguments:
        #       thread_FI : the firebase object instance as passed on from Listener class   
        # Method:
        #       set the firebase instance of MyThread class to the firebase instance of the Listener class
        # Output:
        #       None

            self.thread_FI = thread_FI

        def set_printing(self, printing=False):

        # Arguments:
        #       printing : the priting instance of the Listener class, if printing is true then print statements will be executed otherwise they'll not be executed  
        # Method:
        #       set the 'printing' instance of MyThread class to the 'printing' instance of the Listener class
        # Output:
        #       None

            self.printing = printing

        def set_loggers(self, logger, labels_logger):

        # Arguments:
        #       logger : logging object that will log generic information regarding successful execution, errors, exceptions and warnings 
        #       labels_logger : logging object that will log image id (same as user id) and labels detected in the image
        # Method:
        #       set the loggers instances of MyThread class to the loggers instances of the Listener class
        #       When MyThread object is formed, the instances of loggers are passed from Listener object and are set here
        #       Hence, the instances will be then same in Listener and MyThread class for logging objects 
        #       
        #       Note:
        #           labels logging objects are inactive on this server because the labels are being logged on the asset selection server along with the image id and assets selected
        # Output:
        #       None

            self.thread_logger = logger
            self.thread_labels_logger = labels_logger

        def set_default_label(self, user_id, event_id, template_name):

        # Arguments:
        #       user_id : the firebase idenfication id of the user
        #       event_id : the event the user is currently playing in
        #       template_name : name of the type of template 
        # Method:       
        #       If any exception occurs in any of the threads due to any error then a default data must be added to vision node in firebase for asset selection server to process
        #       A predefined default data is updated in the vision node on firebase
        #       
        #       Note:
        #           default labels in this case is an empty list
        #           this empty list triggers the asset selection server to add default data of assets for the user on firebase 
        # Output: 
        #       None 

            print(self._CLASS_TAG + " - set_default_label()")

            default_data = { 
                    self._EVENT_ID_THREAD : event_id,
                    self._LABEL_LIST_THREAD : [],
                    self._TEMPLATE_NAME_THREAD : template_name
            }

            # print('data - User class : ', default_data)

            self.thread_FI.child(self._VISION_NODE_THREAD).update({user_id: default_data})

    #End of Inner MyThread Class


    #FUNCTIONS OF OUTER CLASS:

    def CreateThread(self, message, threadid):

        # Arguments:
        #       message : the change received by the onChange function, message contains the information regarding change that has occured in the 'listened' node
        #       threadid : the id of the thread for identification 
        # Method:
        #       This function is called on change that occurs in the 'listened' node
        #       This function is called when the change tha has occurred is the change that needs to be processed further
        #       Change is passed on to this functio for further processing
        #       The change occured i.e the data added or edited can be seen inside of 'message'
        #       'message' will contain:
        #                   event_type: put(push), set, patch, delete
        #                   path : path of the node changed/edited
        #                   data : the data added/edited
        #       Required information is extracted from the variable 'message' such as event_type, path, data
        #                   path : is used to get the user_id
        #                   data : is used to get the event_id, data as a whole is also passed on to other functions for further processing
        #       thread_name is generated using user_id, event_id and current_time, this is to keep track of the thread and for case where an exception may occur
        #       A thread is then created using MyThread class and the 'CallFunction' is called
        #       Required data is passed on to the CallFunction with each thread for further processing
        #       Note: 
        #                   MyThread class is a class inside the Listener class with its own references
        #                   Therefore, we have to intialize its FI, printing and logger objects which we are doing in the 'set_...' functions respectively
        # Output:
        #       None

        event_type = message.event_type
        path = message.path
        task = path.split('/')
        data = message.data
        user_id = task[1]
        event_id = data[self._EVENT_ID]
        template_name = data[self._TEMPLATE_NAME]

        current_time = datetime.datetime.now().isoformat()                                  #get current time
        thread_name = user_id + "/" + event_id + "/" + template_name + "/" + current_time   #thread name becomes 'task_id/user_id/event_id/curren_time'

        print("CreateThread - " + thread_name)
        if self.printing==True: print(self._CLASS_TAG + ' - CreateThread()')
        self.thread = self.MyThread(target=self.CallFunction, name = thread_name, args=(event_type, path, data))
        self.thread.set_FI(self.FI)
        self.thread.set_printing(self.printing)
        self.thread.set_loggers(self.logger, self.labels_logger)                            # pass the FI instance and set is as the thread_FI for the particular thread, to access it later to update user variables
        self.thread.start()                                                                 #start the thread
        print("New thread started")

    def CallFunction(self, event_type, path, data):

        # Arguments:
        #      event_type: put(push), set, patch, delete
        #      path : path of the node changed/edited
        #      data : the data added/edited   
        # Method:
        #       This function is called when a new thread is started triggered by any change that occurs in the 'listened' node 
        #       Whenever a new thread is started/created, this function is called first
        #       This function will initiate YOLO Class and then use the results received to update user node in firebase
        #       YOLO class will
        #               download image from the image url
        #               detect objects in the image 
        #               return the labels to this CallFunction
        #       Once labels are received, the user node is updated in firebase and the ask is deleted from FileUrk node
        # Output:
        #       None

        event_type = event_type
        path = path
        task = path.split('/')
        user_id = task[1]
        data = data
        if self.printing==True: print('data: ',  data)
        event_id = data[self._EVENT_ID]
        url = data[self._URL]
        template_name = data[self._TEMPLATE_NAME]

        if self.printing==True:
            print("CallFunction - " )                                                       #this gives the data that has been added to taskQueue in the form of a dictionary
            print("message: " , data)
            print("event: ", event_type)
            print("path: ", path)
            print("userid: ", user_id)
            print("event_id: ", event_id)
            print("url: ", url)
            print("template_name: ", template_name)
            print(self._CLASS_TAG + ' - CallFunction()')

        if(path != '/' and event_type == 'put'):
            if self.printing==True: print("Call function - perform asset task")

            labels_list = self.YOLO_Model.object_detection(url)
            if self.printing==True: print("CallFunction - Labels List: ", labels_list)
            self.Add_Data_to_Vision_Node(user_id, event_id, labels_list, template_name)
            self.delete_task_fileUrl(user_id)

            self.logger.info("Start process for user {} and event {}".format(user_id, event_id))


    def Add_Data_to_Vision_Node(self, user_id, event_id, labels_list, template_name):
        if self.printing==True: print(self._CLASS_TAG + " - Add_Data_to_Vision_Node()")
        data = { 
                    self._EVENT_ID : event_id,
                    self._LABEL_LIST : labels_list,
                    self._TEMPLATE_NAME : template_name
            }

        if self.printing==True: print('data - User class : ', data)

        self.FI.child(self._VISION_NODE).child(user_id).update(data)

    def delete_task_fileUrl(self, user_id):

        # Arguments:
        #       None   
        # Method:
        #       delete the task, once completed, from the firebase node (_FILE_URL_NODE)
        # Output:
        #       None

        print(self._CLASS_TAG + " - delete_task()")

        self.FI.child(self._FILE_URL_NODE).child(user_id).delete()


    def onChange(self, message):                    #this class is called on any change that occurs in the 'listened' node
        #extract required stuff from 'message'
        event_type = message.event_type
        path = message.path
        task = path.split('/')
        data = message.data                         #this gives the data that has been added to taskQueue in the form of a dictionary

        if self.printing==True:                   
            print("message: " , data)
            print("event: ", event_type)
            print("path: ", path)
            print("task: ", task)
            
            print(self._CLASS_TAG + ' - onChange()')

        if(path != '/' and event_type == 'put'  and data != None and path != 'refresh_token'):
            if self.printing==True: print("onChange - perform asset task")

            self.no_of_processes += 1                                   #increment the number of threads
            thread_id = 1                                               #increments the thread_id
            self.CreateThread(message, thread_id)                       #create a thread - call the function
            print("NO OF THREADS: ", self.no_of_processes)
