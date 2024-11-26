import asyncio
import logging

from tapsdk import TapSDK, TapInputMode
import traceback

from threads.KeyboardThread import run_keyboard_thread, queue, KeyboardThreadSupplier
from model.AkimboModel import AkimboModel
from config.AkimboConfig import deserialize_config

config = deserialize_config("config.yaml")
model = AkimboModel(config, KeyboardThreadSupplier(queue))

tap_instance = {}
tap_identifiers = []

logging.basicConfig(level=logging.INFO)


def on_connect(identifier, name, fw):
    print(identifier + " Tap: " + str(name), " FW Version: ", fw)
    if identifier not in tap_identifiers:
        tap_identifiers.append(identifier)
    print("Connected taps:")
    for identifier in tap_identifiers:
        print(identifier)


def on_disconnect(identifier):
    print(f"Tap {identifier} has disconnected")
    if identifier in tap_identifiers:
        tap_identifiers.remove(identifier)
    for identifier in tap_identifiers:
        print(identifier)


def on_tap_event(identifier, tapcode):
    try:
        model.process(int(tapcode))
    except Exception as error:
        print("Error processing tapcode")
        print(error)
        print(traceback.format_exception(type(error), error), error.__traceback__)


def main():
    global tap_instance
    tap_instance = TapSDK()
    tap_instance.run()
    tap_instance.register_connection_events(on_connect)
    tap_instance.register_disconnection_events(on_disconnect)
    tap_instance.register_tap_events(on_tap_event)
    tap_instance.set_input_mode(TapInputMode("controller"))


if __name__ == "__main__":
    main()
    run_keyboard_thread()
    print(id(queue))
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_forever()