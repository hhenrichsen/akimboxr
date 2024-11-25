from typing import Any, Callable, Dict
from .AkimboConfig import (
    AkimboConfig,
    ConfigActionType,
    ConfigMapEntry,
    ConfigMapEntryType, ConfigLayer,
)
from pynput.keyboard import Controller
import asyncio

from .AkimboTapHandler import AkimboTapHandler


# Converts a 5-bit integer to a unicode representation of a key
def key_to_unicode(key: int) -> str:
    return "".join(["●" if (key >> i) & 1 else "○" for i in range(5)])


class AkimboLayer:
    def __init__(
            self,
            name: str,
            actions: Dict[int, AkimboTapHandler],
            transparent: bool = False,
    ):
        self.name = name
        self.actionMap = actions
        self.__transparent = transparent

    def process(self, tapcode: int, down_layer: Callable[[], None]):
        print(f"Process {self.name}")
        if tapcode in self.actionMap:
            print(f"Running {tapcode}")
            if self.__transparent:
                self.actionMap[tapcode].execute(down_layer)
            else:
                self.actionMap[tapcode].execute(lambda: None)

        print(f"End {self.name}")

    def __repr__(self):
        return f"AkimboLayer(name={self.name})"


class AkimboModel:
    def __init__(self, config: AkimboConfig, loop: asyncio.AbstractEventLoop):
        self.__layers = {}
        self.__active_layers = []
        self.__timeout = config.timeout / 1000
        self.__keyboard = Controller()
        self.__loop = loop

        for layerName in config.layers:
            config_layer = config.layers[layerName]
            layer = self._build_map_layer(config_layer)
            print(f"Built layer {layer.name}")
            self.__layers[layerName] = layer
            if config_layer.default:
                self.__active_layers.append(layer)


        print("Active layers:")
        for key, entry in sorted(self.__active_layers[-1].actionMap.items(), key=lambda x: x[0]):
            print(f"Key: {key_to_unicode(key)} Entry: {entry}")

    def process(self, tapcode: int):
        # Process the tapcode through the active layers, passing the next layer as a callback
        active_layers = [*self.__active_layers]

        def down_layer():
            # print(" ".join([x.name for x in active_layers]))
            if len(active_layers) > 0:
                active_layers.pop().process(tapcode, down_layer)

        down_layer()

    def _build_map_layer(self, layer: ConfigLayer):
        key_entries: Dict[int, Any] = {}
        for entry in layer.map:
            if entry.code not in key_entries:
                key_entries[entry.code] = []
            key_entries[entry.code].append(entry)

        key_tasks = {}
        for code in key_entries:
            single = next(
                filter(
                    lambda x: x.type == ConfigMapEntryType.Single,
                    key_entries[code],
                ),
                None,
            )
            single_action = (
                self._build_action(single, code) if single is not None else None
            )
            double = next(
                filter(
                    lambda x: x.type == ConfigMapEntryType.Double,
                    key_entries[code],
                ),
                None,
            )
            double_action = (
                self._build_action(double, code) if double is not None else None
            )
            triple = next(
                filter(
                    lambda x: x.type == ConfigMapEntryType.Triple,
                    key_entries[code],
                ),
                None,
            )
            triple_action = (
                self._build_action(triple, code) if triple is not None else None
            )

            key_tasks[code] = AkimboTapHandler(
                single_action, double_action, triple_action, self.__loop, self.__timeout, code
            )
        return AkimboLayer(layer.name, key_tasks, layer.transparent)

    def _build_action(
            self, entry: ConfigMapEntry, code: int
    ) -> Callable[[Callable], None]:
        pre_tasks = []
        post_tasks = []
        for action in entry.actions:
            if action.type == ConfigActionType.Press:

                print(f"Task for {code} will be {action.keys}")

                def pre():
                    for chord in action.keys:
                        for press in chord:
                            print(f"Pressing {press}")
                            self.__keyboard.press(press)

                pre_tasks.append(pre)

                def post():
                    for chord in action.keys:
                        for release in reversed(chord):
                            print(f"Releasing {release}")
                            self.__keyboard.release(release)

                post_tasks.append(post)

            if action.type == ConfigActionType.PushLayer:
                # TODO: Figure out how to escape the layer once you get into it
                key = action.layer
                print(f"Task for {code} will be move to {key}")

                def run():
                    if key in self.__layers:
                        print(f"Pushing layer {key}")
                        self.__active_layers.append(self.__layers[key])

                pre_tasks.append(run)

            if action.type == ConfigActionType.PopLayer:
                def run():
                    if len(self.__active_layers) > 1:
                        self.__active_layers.pop()

                pre_tasks.append(run)

            if action.type == ConfigActionType.TopLayer:
                key = action.layer
                print(f"Task for {code} will be move to {key}")

                def run():
                    if key in self.__layers:
                        self.__active_layers = filter(lambda x: x.name != key, self.__active_layers)
                        self.__active_layers.append(self.__layers[key])

                pre_tasks.append(run)


        def run(down_layer):
            print(f"Running {code}")
            [setup() for setup in pre_tasks]
            down_layer()
            [teardown() for teardown in post_tasks]

        return run
