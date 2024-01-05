import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os
import logging




class Root:

    _DB_URL = "https://madhuntar.firebaseio.com/"
    _JSON = "madhuntar-firebase-adminsdk-fs6c8-2202369f34.json"
    _LOOP_LIMIT = 60


    def __init__(self, root=None, path='/'):
        if(not root == None):
            self.root = root
            self.db = db
            self.path = path
        else:
            self.app = None
            self.initialize(self._DB_URL, self._JSON)
            self.path = ''

    def initialize(self, databaseURL, jsonFile):
        print("Initializing")
        logging.info("FI (Firebase) object initialized")

        basepath = os.path.dirname(__file__)
        filepath = os.path.abspath(os.path.join(basepath,jsonFile))
        print(filepath)

        cred = credentials.Certificate(filepath)
        firebase_admin.initialize_app(cred, {"databaseURL": databaseURL})
        self.app = firebase_admin.get_app()
        print(type(self.app))
        self.root = db.reference(app = self.app)
        print("root: ", self.root)
        self.db = db
        print(self.root.path)
        # print(db)


    def __repr__(self):
        return "Firebase admin path [{}]".format(self.path)


    def child(self, *args):
        #Clues_Solved_user = db.reference('users/{0}'.format(str_bacpack)).get()
        try:
            paths = [self.path]
            paths.extend(args)
            new_path = '/'.join([str(path) for path in paths if path])
            output = self.__class__(db.reference(new_path), new_path)

            return output

        except Exception as Argument:
            print("--------------------------------------CHILD ERROR: ", Argument)
            #logging.warning("Issue in child() --- ", Argument)
            return None

    def get(self, *args, **kwargs):
        try:
            self.root = db.reference(path=self.path)
            # print("Get Path: ", self.path)
            output = self.root.get(*args, **kwargs)
            return output

        except Exception as Argument:
            print("-------------------------------------- GET ERROR: ", Argument)
            #logging.warning("Issue in get() --- ", Argument)
            return None


    def getPath(self):
        return self.db.path

    def push(self, *args, **kwargs):
        self.root = db.reference(path=self.path)
        self.latest_result = self.root.push(*args, **kwargs)

        return self

    def set(self, *args, **kwargs):
        self.root = db.reference(path=self.path)
        self.latest_result = self.root.set(*args, **kwargs)

        return self

    def update(self, *args, **kwargs):
        try:
            self.root = db.reference(path=self.path)
            self.latest_result = self.root.update(*args, **kwargs)
            return self

        except Exception as Argument:
            print("--------------------------------------UPDATE ERROR: ", Argument)
            #logging.warning("Issue in update() --- ", Argument)
            return None

    def delete(self, *args, **kwargs):
        try:
            self.root = db.reference(path=self.path)
            self.latest_result = self.root.delete(*args, **kwargs)
            return self

        except Exception as Argument:
            print("-------------------------------------- DELETE ERROR: ", Argument)
            #logging.warning("Issue in delete() --- ", Argument)
            return None

    def streamListener(self, call_function, node):
        self.root = db.reference(path=self.path)
        print(self.root)
        self.root.child(node).listen(call_function)
        #logging.info("Streaming of " + self._TASKQUEUE + " started")

    def streamNode(self, call_function):
        self.root = db.reference(path=self.path)

        self.root.child("names").listen(call_function)



# FI = Interface()
# # FI.child('CV/abc').set({'testdata': '12345'})
# # FI.child('CV').child('abc').push({'testdata3': '12345'})
# # print(FI.getPath())
# FI.child('CV').child('abc').update({'testdata' : '123456'})
