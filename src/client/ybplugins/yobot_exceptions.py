# coding=utf-8
class FileError(IOError):
    def __init__(self, s="file error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg

class ServerError(Exception):
    def __init__(self, s="server error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg

class CodingError(IOError):
    def __init__(self, s="coding error"):
        super().__init__(self)
        self.error_msg = s

class InputError(ValueError):
    def __init__(self, s="input error"):
        super().__init__(self)
        self.error_msg = s

    def __str__(self):
        return self.error_msg
