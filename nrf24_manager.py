#! venv/bin/python

import yaml
import paho.mqtt.client as mqtt
import logging
import sys
import time
import threading
from RF24 import RF24
import RPi.GPIO as GPIO

class Nrf24Manager:

    def __init__(self, radio_config_file: str, mqtt_config_file: str):
        # load config
        with open(radio_config_file, 'r') as radio_config_file_content:
            self.__radio_config = yaml.safe_load(radio_config_file_content)
        with open(mqtt_config_file, 'r') as mqtt_config_file_content:
            self.__mqtt_config = yaml.safe_load(mqtt_config_file_content)
        # setup led
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.__radio_config["led_pin"], GPIO.OUT)
        GPIO.output(self.__radio_config["led_pin"], GPIO.LOW)
        self.__threaded_blink(num_blinks=3)
        # setup writing interface
        self.__writing_triggered = False
        self.__writing_payload = None
        # setup mqtt
        self.__client = mqtt.Client()
        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message
        self.__client.username_pw_set(self.__mqtt_config["user"], password=self.__mqtt_config["password"])
        logging.info(f"Try to connected to MQTT broker \"{self.__mqtt_config['host']}\" at port \"{self.__mqtt_config['port']}\".")
        self.__client.connect(self.__mqtt_config["host"], self.__mqtt_config["port"], 60)
        self.__client.loop_start()
        # setup rf24 radio
        self.__radio = RF24(self.__radio_config["ce_pin"], self.__radio_config["cs_pin"])
        self.__radio.setRetries(self.__radio_config["retry_delay"], self.__radio_config["max_retries"])
        self.__radio.begin()
        logging.info(f'Opening writing pipe 0 with address "{self.__radio_config["pipes"]["writing"]["address"]}".')
        self.__radio.openWritingPipe(self.__radio_config["pipes"]["writing"]["address"].encode('utf-8'))
        for pipeIdx, readingPipe in enumerate(self.__radio_config["pipes"]["reading"]):
            logging.info(f'Opening reading pipe {pipeIdx + 1} with address "{readingPipe["address"]}".')
            self.__radio.openReadingPipe(pipeIdx + 1, readingPipe["address"].encode('utf-8'))
        self.__radio.startListening()
        # enter loop
        while True:
            self.__loop()

    def __loop(self):
        # receive message
        available, pipe = self.__radio.available_pipe()
        if available:
            receive_payload = self.__radio.read(self.__radio_config["payload_length"])
            receive_payload_str = receive_payload.split(b'\x00', 1)[0].decode('utf-8')
            logging.info(f'Got radio message in pipe {pipe} with payload "{receive_payload_str}".')
            pipe_config = self.__radio_config["pipes"]["reading"][pipe - 1]
            topic = pipe_config["topic"]
            if receive_payload_str.startswith("["):
                if receive_payload_str.startswith("[confirm]"):
                    logging.info('Message confirmed.')
                    return
                else:
                    subtopic, receive_payload_str = receive_payload_str.split("] ")
                    topic += subtopic.replace("[", "")
            logging.info(f"Pubish payload \"{receive_payload_str}\" in MQTT topic \"{topic}\".")
            self.__client.publish(topic, payload=receive_payload_str, qos=2)
            if pipe_config["blink"]:
                self.__threaded_blink(2)
        # send message
        if self.__writing_triggered:
            self.__writing_triggered = False
            logging.info(f'Send payload "{self.__writing_payload.encode("utf-8")}" via radio.')
            self.__radio.stopListening()
            self.__radio.write(self.__writing_payload.encode('utf-8'))
            self.__radio.startListening()
            if self.__radio_config["pipes"]["writing"]["blink"]:
                self.__threaded_blink(1)

    def __threaded_blink(self, num_blinks: int):
        blink_thread = threading.Thread(target=self.__blink, args=(num_blinks,))
        blink_thread.start()

    def __blink(self, num_blinks: int):
        for blink_idx in range(num_blinks):
            GPIO.output(self.__radio_config["led_pin"], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(self.__radio_config["led_pin"], GPIO.LOW)
            time.sleep(0.1)

    def __on_connect(self, client, _userdata, _flags, return_code):
        logging.info(f"Connected to MQTT broker with result code \"{return_code}\".")
        client.subscribe(self.__radio_config["pipes"]["writing"]["topic"])
        logging.info(f"Subscribed to MQTT topic {self.__radio_config['pipes']['writing']['topic']}.")

    def __on_message(self, _client, _userdata, msg):
        payload = msg.payload.decode("utf-8")
        logging.info(f"MQTT writing command with payload: {payload}")
        self.__writing_triggered = True
        self.__writing_payload = payload


if __name__ == "__main__":
    # setup logging
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S', stream=sys.stdout)
    logging.info("Start Nrf24 Manager.")
    radio_config_file = "radio_config.yaml"
    mqtt_config_file = "./mqtt_config.yaml"
    Nrf24Manager(radio_config_file=radio_config_file, mqtt_config_file=mqtt_config_file)
