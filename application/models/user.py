from mongokit import *
import datetime
import hashlib, hmac, base64, re
import datetime
from lib.mongo import Mongo

'''
    Remember to register with mongo.py
'''




'''
normalizes a username or email address
'''
def normalize(username):
    if not username :
        return None
    #allow legal email address
    name = username.strip().lower()
    name = re.sub(r'[^a-z0-9\\.\\@_\\-~#]+', '', name)
    name = re.sub('\\s+', '_',name)
    
    #don't allow $ and . because they screw up the db.
    name = name.replace(".", "")
    name = name.replace("$", "")
    return name;
    
    
class User(Document):
    structure = {
                 '_id':unicode,
                 'email':unicode,
                 'access':list,
                 'password':unicode,
                 'created_at':datetime.datetime,
                 'history' : {
                              'last_login' : datetime.datetime,
                              'num_logins' : long
                              },
                 'timezone':unicode,
                 'timespan':unicode,
                 'suspended_at':datetime.datetime,
                 }
    use_dot_notation=True
    
    @staticmethod
    def normalize(username):
        return normalize(username)
        
    
    @staticmethod
    def lookup(username):
        return Mongo.db.ui.users.User.find_one({'_id' : normalize(username)})
        
        
    '''
    creates a new user instance. unsaved
    '''
    @staticmethod
    def instance(username, password):
        
        username = normalize(username)
        user = User()
        user.access = [username]
        user['_id'] = username
        user.password = hashlib.sha1(password).hexdigest()
        user.created_at = datetime.datetime.utcnow()
        user.history = {
                        'num_logins' : 0
                        }
        return user
    
    def has_role(self, role):
        if not self.access:
            return False
        if isinstance(role, basestring):
            return role in self.access
        else:
            for r in role:
                if r in self.access:
                    return True
    
    def name(self):
        return self._id
    
    def get_timezone(self):
        tz = self.get('timezone', None)
        if tz :
            return tz
        return 'America/New_York'
                
    def is_suspended(self):
        if self.get('suspended_at', None) == None :
            return False
        return self.suspended_at < datetime.datetime.utcnow()
     