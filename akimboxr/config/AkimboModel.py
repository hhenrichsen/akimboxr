from typing import Any, Callable, Dict, List
from .AkimboConfig import (
    AkimboConfig,
    ConfigActionType,
    ConfigMapEntry,
    ConfigMapEntryType, ConfigLayer, ConfigAction,
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
            action_map: Dict[int, AkimboTapHandler],
            transparent: bool = False,
            enter_actions: List[Callable[[], None]] | None = None,
            exit_actions: List[Callable[[], None]] | None = None,
    ):
        if enter_actions is None:
            enter_actions = []
        if exit_actions is None:
            exit_actions = []
        self.name = name
        self.__actionMap = action_map
        self.__enter_actions = enter_actions
        self.__exit_actions = exit_actions
        self.__transparent = transparent

    def is_transparent(self):
        return self.__transparent

    def process(self, tapcode: int):
        print(f"Process {self.name}")
        if tapcode in self.__actionMap:
            print(f"Running {tapcode}")
            if self.__transparent:
                self.__actionMap[tapcode].execute()
            else:
                self.__actionMap[tapcode].execute()

        print(f"End {self.name}")

    def would_process(self, tapcode: int):
        return tapcode in self.__actionMap

    def __repr__(self):
        return f"AkimboLayer(name={self.name})"

    def __enter__(self):
        print(f"Enter {self.name}")
        for action in self.__enter_actions:
            print(f"Run exit action {self.name}")
            action()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Exit {self.name}")
        for action in self.__exit_actions:
            print(f"Run exit action {self.name}")
            action()



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
            self.__layers[layerName] = layer
            if config_layer.default:
                self.__active_layers.append(layer)

    def process(self, tapcode: int):
        # Process the tapcode through the active layers, passing the next layer as a callback
        active_layers: List[AkimboLayer] = [*self.__active_layers]

        def down_layer():
            if len(active_layers) < 1:
                return
            layer = active_layers.pop()
            with layer:
                if layer.would_process(tapcode):
                    layer.process(tapcode)
                elif layer.is_transparent():
                    down_layer()

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

        enter_actions = []
        exit_actions = []
        print(f"{layer.name} actions: {len(layer.actions)}")
        for action in layer.actions:
            enter_action, exit_action = self._build_split_action(action)
            if enter_action is not None:
                enter_actions.append(enter_action)
            if exit_action is not None:
                exit_actions.append(exit_action)

        return AkimboLayer(layer.name, key_tasks, layer.transparent, enter_actions, exit_actions)

    def _build_split_action(self, action: ConfigAction):
        if action.type == ConfigActionType.Press:
            print("Building split press action")

            def pre():
                for chord in action.keys:
                    for press in chord:
                        print(f"Pressing {press}")
                        self.__keyboard.press(press)

            def post():
                for chord in action.keys:
                    for release in chord:
                        print(f"Releasing {release}")
                        self.__keyboard.release(release)

            return pre, post
        pass

    def _build_action(
            self, entry: ConfigMapEntry, code: int
    ):
        tasks = []
        for action in entry.actions:
            if action.type == ConfigActionType.Press:

                print(f"Task for {code} will be {action.keys}")

                def run():
                    for chord in action.keys:
                        for press in chord:
                            print(f"Typing {press}")
                            self.__keyboard.press(press)
                        for release in chord:
                            self.__keyboard.release(release)

                tasks.append(run)

            if action.type == ConfigActionType.PushLayer:
                key = action.layer
                print(f"Task for {code} will be move to {key}")

                def run():
                    if key in self.__layers:
                        print(f"Pushing layer {key}")
                        self.__active_layers.append(self.__layers[key])

                tasks.append(run)

            if action.type == ConfigActionType.PopLayer:
                def run():
                    if len(self.__active_layers) > 1:
                        self.__active_layers.pop()

                tasks.append(run)

            if action.type == ConfigActionType.TopLayer:
                key = action.layer
                print(f"Task for {code} will be move to {key}")

                def run():
                    if key in self.__layers:
                        self.__active_layers = filter(lambda x: x.name != key, self.__active_layers)
                        self.__active_layers.append(self.__layers[key])

                tasks.append(run)

        def run():
            [task() for task in tasks]

        return run
