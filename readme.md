# Nrf24Manager

This manager can be configured to send and receive messages via a NRF24 radio. The received messages are forwarded via MQTT. Also the manager listens for commands via MQTT to send them via the NRF24 radio. Therefore this manager can be regarded as a bridge between the NRF24 radio and MQTT.

## Setup

Follow the instructions on https://tmrh20.github.io/RF24/Python.html to install the RF24 lib for python. Install the manager via

```commandline
git clone https://github.com/heidenbloed/nrf24Manager.git
```

Adapt the MQTT settings via

```commandline
cd nrf24Manager
cp mqtt_config_sample.yaml mqtt_config.yaml
nano mqtt_config.yaml
```

Adapt the RF24 settings via

```commandline
nano radio_config.yaml
```

Install the service via

```commandline
install_service.sh
```