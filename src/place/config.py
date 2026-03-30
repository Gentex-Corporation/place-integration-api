import decouple

REGION = decouple.config("AWS_REGION", default="us-east-2")
SERVICE = decouple.config("AWS_SERVICE", default="iotdevicegateway")
ALGORITHM = decouple.config("AWS_ALGORITHM", default="AWS4-HMAC-SHA256")
SCHEME = decouple.config("AWS_SCHEME", default="wss")
PATH = decouple.config("AWS_PATH", default="/mqtt")
EXPIRE_SEC = decouple.config("AWS_EXPIRE_SEC", default=86400)
KEEP_ALIVE_SEC = decouple.config("AWS_KEEP_ALIVE_SEC", default=30)
FULFILLMENT_URL = decouple.config("AWS_FULFILLMENT_URL", default="https://mk9ls6wuk9.execute-api.us-east-1.amazonaws.com/prod/fulfillment")
IOT_ENDPOINT = decouple.config("AWS_IOT_ENDPOINT", default="a184o6067c4nnz-ats.iot.us-east-2.amazonaws.com")
AWS_REGION = decouple.config("AWS_REGION", default="us-east-2")
COGNITO_USER_POOL_ID = decouple.config("AWS_COGNITO_USER_POOL_ID", default="us-east-2_Ahp4pm1iv")
COGNITO_CLIENT_ID = decouple.config("AWS_COGNITO_CLIENT_ID", default="5tuofl4e9rhtuor33dlau9jnp6")
COGNITO_IDENTITY_POOL_ID = decouple.config("AWS_COGNITO_IDENTITY_POOL_ID", default="us-east-2:2ac90fe6-2940-432b-824f-8d6bb785d787")

