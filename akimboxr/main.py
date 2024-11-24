from tapsdk import TapSDK, TapInputMode
import asyncio
from config.AkimboModel import AkimboModel
from config.AkimboConfig import deserialize_config

loop = asyncio.new_event_loop()
config = deserialize_config("config.yaml")
model = AkimboModel(config, loop)

tap_instance = {}
tap_identifiers = []


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
    print(identifier, str(tapcode))
    try:
        model.process(int(tapcode))
    except Exception as e:
        print("Error processing tapcode")
        print(e)
    if int(tapcode) == 17:
        sequence = [500, 200, 500, 500, 500, 200]
        tap_instance.send_vibration_sequence(sequence, identifier)


def main():
    global tap_instance
    tap_instance = TapSDK()
    tap_instance.run()
    tap_instance.register_connection_events(on_connect)
    tap_instance.register_disconnection_events(on_disconnect)
    tap_instance.register_tap_events(on_tap_event)
    tap_instance.set_input_mode(TapInputMode("controller"))

    while True:
        pass


if __name__ == "__main__":
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
