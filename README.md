# Place integration API

This project contains a python API to connect MQTT data from Place devices to Place's Home Assistant integration.


## Setup

This repo utilizes VS Code [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) so you don't need to alter your global python environment.

## Installing dependencies

Use `pip` to install required dependencies by running `pip install -r requirements.txt` from the project root.

## Updating dependencies

During the course of development, if new packages are added, it's recommended to update [`requirements.txt`](./requirements.txt) by running `pip freeze > requirements.txt`.


## Refreshing MQTT credentials

For long-lived connections, provide a synchronous callback that returns fresh
`Credentials` using a valid Cognito ID token:

```python
client = MqttClient(
    endpoint=iot_endpoint,
    credentials=initial_credentials,
    credentials_provider=refresh_credentials,
)
```

The callback runs before each reconnect attempt, usually on the MQTT network
thread. If it raises, Paho retries without using stale credentials. The caller
must refresh the ID token as needed. Async applications should bridge safely to
their event loop. Stopping the MQTT loop waits for an in-flight callback.
Without a provider, the initial credentials are reused.


## Requesting a device shadow

Call `PlaceMessages.subscribe_shadow_and_get(thing_name)` from the MQTT client's
`on_connect` callback. It subscribes to the device's shadow topics and sends the
shadow GET only after the broker acknowledges the subscription. The `on_connect`
callback is also invoked on reconnect, so it should subscribe every device again.
Rejected subscriptions are logged and do not send a GET.
