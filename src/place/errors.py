"""Errors for the Place API."""


class PlaceApiError(Exception):
    """Base error for Place API failures."""


class PlaceLoginError(PlaceApiError):
    """Raised when login fails."""


class PlaceInvalidCredentialsError(PlaceLoginError):
    """Raised when credentials are rejected or the account needs attention."""


class PlaceLoginConnectionError(PlaceLoginError):
    """Raised when the login service is unavailable."""


class PlaceCredentialExchangeError(PlaceApiError):
    """Raised when AWS IoT credentials cannot be obtained."""


class PlaceCredentialExchangeAuthError(PlaceCredentialExchangeError):
    """Raised when the credentials exchange rejects the user's identity."""


class PlaceCredentialExchangeConnectionError(PlaceCredentialExchangeError):
    """Raised when the credentials exchange service is unavailable."""


class PlaceFulfillmentError(PlaceApiError):
    """Raised when the fulfillment API reports a business-logic failure."""


class PlaceMqttConnectionError(PlaceApiError):
    """Raised when the MQTT broker rejects or fails to establish a connection."""


class PlaceMqttSubscriptionError(PlaceApiError):
    """Raised when an MQTT subscription cannot be sent."""
