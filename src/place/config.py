import decouple

REGION = decouple.config("AWS_REGION", default="us-east-2")
SERVICE = decouple.config("AWS_SERVICE", default="iotdevicegateway")
ALGORITHM = decouple.config("AWS_ALGORITHM", default="AWS4-HMAC-SHA256")
SCHEME = decouple.config("AWS_SCHEME", default="wss")
PATH = decouple.config("AWS_PATH", default="/mqtt")
EXPIRE_SEC = decouple.config("AWS_EXPIRE_SEC", default=86400)
KEEP_ALIVE_SEC = decouple.config("AWS_KEEP_ALIVE_SEC", default=30)
# STAGING
FULFILLMENT_URL = decouple.config("AWS_FULFILLMENT_URL", default="https://vrvzv4dc94.execute-api.us-east-1.amazonaws.com/prod/fulfillment")
# Note: must be the regional IoT endpoint for now. Currently the custom IoT endpoint/domain configuration uses ApplicationProtocol.SECURE_MQTT
# a second domain configuration must be created for ApplicationProtocol.MQTT_WSS in order to use the custom IoT endpoint instead.
# STAGING
IOT_ENDPOINT = decouple.config("AWS_IOT_ENDPOINT", default="a3e12ykhjozrz1-ats.iot.us-east-2.amazonaws.com")
# STAGING
COGNITO_USER_POOL_ID = decouple.config("AWS_COGNITO_USER_POOL_ID", default="us-east-2_XrP6xRu3g")
# STAGING
COGNITO_CLIENT_ID = decouple.config("AWS_COGNITO_CLIENT_ID", default="3nortia061l8o9h29bgf6ajqgj")
# STAGING
COGNITO_IDENTITY_POOL_ID = decouple.config("AWS_COGNITO_IDENTITY_POOL_ID", default="us-east-2:9ad99cde-4280-47f2-93f9-f0bf87450d22")
# STAGING
OAUTH2_TOKEN_URL = decouple.config("OAUTH2_TOKEN_URL", default="https://auth.staging.connectedsmoke.com/oauth2/token")