class LoginFailedException(RuntimeError):
    text = ''
    def __init__(self, details):
        self.text = 'LoginFailedException: ' + str(details)

class TradeLimitExceededException(RuntimeError):
    text = ''
    def __init__(self, details):
        self.text = 'TradeLimitExceededException: ' + str(details)

class InvalidPriceRangeException(RuntimeError):
    text = ''
    def __init__(self, text):
        self.text = 'InvalidPriceRangeException: ' + str(text)

class ServiceUnavailibleException(RuntimeError):
    text = ''
    def __init__(self, text):
        self.text = 'ServiceUnavailibleException: ' + str(text)

class UnkownErrorExceprion(RuntimeError):
    text = ''
    def __init__(self, text):
        self.text = 'UnkownErrorExceprion: ' + str(text)