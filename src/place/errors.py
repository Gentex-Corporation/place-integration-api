"""Errors for the Place API."""


class PlaceApiError(Exception):
    """Base error for Place API failures."""


class PlaceFulfillmentError(PlaceApiError):
    """Raised when the fulfillment API reports a business-logic failure."""
