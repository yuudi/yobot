# coding=utf-8
class File_error(IOError):
    def __init__(self, s="file error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg

class Server_error(Exception):
    def __init__(self, s="server error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg

class Coding_error(IOError):
    def __init__(self, s="coding error"):
        super().__init__(self)
        self.error_msg = s

class Input_error(ValueError):
    def __init__(self, s="input error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg

class Exit(Exception):
    def __init__(self, s="Exit"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg