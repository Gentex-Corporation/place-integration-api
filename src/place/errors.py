"""Errors for the Place API."""


class PlaceApiError(Exception):
    """Base error for Place API failures."""


class PlaceFulfillmentError(PlaceApiError):
    """Raised when the fulfillment API reports a business-logic failure."""


class PlaceMqttConnectionError(PlaceApiError):
    """Raised when the MQTT broker rejects or fails to establish a connection."""
