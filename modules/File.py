class File():

    def __init__(self, name, mode='w'):
        self.f = open(name, mode, buffering=1)
        
    def write(self, string, newline=True):
        if newline:
            self.f.write(string + '\n')
        else:
            self.f.write(string)
    def close(self):
        self.f.close()