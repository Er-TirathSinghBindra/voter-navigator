class CivicNavigatorError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CivicAPIError(CivicNavigatorError):
    """Exception raised for errors in the Civic Information API."""
    pass

class CalendarAPIError(CivicNavigatorError):
    """Exception raised for errors in the Google Calendar API."""
    pass

class WalletAPIError(CivicNavigatorError):
    """Exception raised for errors in the Google Wallet API."""
    pass

class TranslationAPIError(CivicNavigatorError):
    """Exception raised for errors in the Google Translation API."""
    pass
