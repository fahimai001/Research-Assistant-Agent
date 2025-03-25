class Passwd:
    def __init__(self, username, uid, gid):
        self.pw_name = username
        self.pw_uid = uid
        self.pw_gid = gid
    

def getpwuid(uid):
    import os
    return Passwd(os.environ.get('USERNAME', 'unknown'), uid, 0)

def getpwnam(name):
    return Passwd(name, 1000, 0)