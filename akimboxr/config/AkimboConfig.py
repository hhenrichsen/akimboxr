from enum import Enum
import yaml
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from pynput.keyboard import Key, KeyCode


class ConfigActionType(Enum):
    Press = "press"
    PushLayer = "pushlayer"
    PopLayer = "poplayer"
    TopLayer = "toplayer"


class ConfigAction:
    def __init__(
        self, type: ConfigActionType, backspace_count: int, layer: str | None, keys: list[list[Key | str]]
    ):
        self.type = type
        self.keys = keys
        self.backspace_count = backspace_count
        self.layer = layer

    @staticmethod
    def build(values: Dict[str, Any]) -> "ConfigAction":
        if "key" in values:
            values["keys"] = [
                [_parse_key(key) for key in chord.split("+")]
                for chord in values["key"].split(",")
            ]
            del values["key"]
        else:
            values["keys"] = []
        values["layer"] = values["layer"] if "layer" in values else None
        values["type"] = ConfigActionType(values["type"])
        values["backspace_count"] = (
            values["backspace_count"] if "backspace_count" in values else 1
        )
        return ConfigAction(**values)

    def __repr__(self):
        return f"""      ConfigAction(type={self.type}, key={self.key})"""


def _parse_key(key: str) -> Key | KeyCode:
    match key:
        case "space" | " ":
            return Key.space
        case "enter" | "return":
            return Key.enter
        case "tab":
            return Key.tab
        case "esc" | "escape":
            return Key.esc
        case "backspace":
            return Key.backspace
        case "delete":
            return Key.delete
        case "insert":
            return Key.insert
        case "home":
            return Key.home
        case "end":
            return Key.end
        case "page_up":
            return Key.page_up
        case "page_down":
            return Key.page_down
        case "up":
            return Key.up
        case "down":
            return Key.down
        case "left":
            return Key.left
        case "right":
            return Key.right
        case "cmd" | "command":
            return Key.cmd
        case "ctrl" | "control":
            return Key.ctrl
        case "alt":
            return Key.alt
        case "shift":
            return Key.shift
        case "plus":
            return KeyCode.from_char("+")
        case "comma":
            return KeyCode.from_char(",")
        case "period":
            return KeyCode.from_char(".")
        case "semicolon":
            return KeyCode.from_char(";")
        case "apostrophe":
            return KeyCode.from_char("'")
        case "backslash":
            return KeyCode.from_char("\\")
        case "slash":
            return KeyCode.from_char("/")
        case _:
            return KeyCode.from_char(key)


class ConfigMapEntryType(Enum):
    Single = "single"
    Double = "double"
    Triple = "triple"


def _parse_code(code: str) -> int:
    c = 0
    if code.isnumeric():
        return int(code)
    for i, ch in enumerate(code):
        if ch == "x" or ch == "●":
            c |= 1 << i
    return c


class ConfigMapEntry:
    def __init__(self, code: int, type: str, actions: List[ConfigAction]):
        self.code = code
        self.type = type
        self.actions = actions

    @staticmethod
    def build(values: Dict[str, Any]) -> "ConfigMapEntry":
        values["code"] = _parse_code(values["code"])
        values["type"] = ConfigMapEntryType(values["type"])
        values["actions"] = (
            [ConfigAction.build(action) for action in values["actions"]]
            if "actions" in values
            else []
        )
        return ConfigMapEntry(**values)

    def __repr__(self):
        actions = ",\n".join(map(str, self.actions))
        return f"""    ConfigMapEntry(code={self.code}, type={self.type}) {"{"}
{actions}
    {"}"}"""


class ConfigLayer:
    def __init__(
        self,
        name: str,
        default: bool,
        transparent: bool,
        map: List[ConfigMapEntry],
        actions: List[ConfigAction],
        extends: str,
    ):
        self.name = name
        self.default = default
        self.map = map
        self.type = type
        self.transparent = transparent
        self.actions = actions
        self.extends = extends

    @staticmethod
    def build(values: Dict[str, Any]) -> "ConfigLayer":
        values["transparent"] = (
            values["transparent"] if "transparent" in values else False
        )
        values["extends"] = values["extends"] if "extends" in values else None
        values["actions"] = (
            [ConfigAction.build(action) for action in values["action"]]
        ) if "action" in values else []
        values["default"] = values["default"] if "default" in values else False
        values["map"] = (
            [ConfigMapEntry.build(entry) for entry in values["map"]]
            if "map" in values
            else []
        )
        return ConfigLayer(**values)

    def __repr__(self):
        keys = ",\n".join(list(map(str, self.map)))
        return f"""  MapLayer(name={self.name}, default={self.default}) {"{"}
{keys}
  {"}"}"""

class ConfigMode(Enum):
    Backspace = "backspace"
    TIMEOUT = "timeout"


class AkimboConfig:
    def __init__(
        self, onehand: bool, mode: str, timeout: int, layers: Dict[str, ConfigLayer]
    ):
        self.onehand = onehand
        self.mode = mode
        self.timeout = timeout
        self.layers = layers

    @staticmethod
    def build(values: Dict[str, Any]) -> "AkimboConfig":
        layers = {}
        if "layers" in values:
            for layer in values["layers"]:
                layers[layer] = ConfigLayer.build(
                    {**values["layers"][layer], "name": layer}
                )
        return AkimboConfig(
            onehand=values["onehand"] if "onehand" in values else True,
            mode=(
                ConfigMode(values["mode"].lower())
                if "mode" in values
                else ConfigMode.Backspace
            ),
            timeout=values["timeout"] if "timeout" in values else 500,
            layers=layers,
        )

    def __repr__(self):
        layers = ",\n".join(map(str, self.layers))
        return f"""AkimboConfig(onehand={self.onehand}, mode={self.mode}, timeouts={self.timeout}) {"{"}
{layers}
{"}"}"""


def deserialize_config(filename: str) -> AkimboConfig:
    with open(filename, "r", encoding="utf-8") as file:
        yaml_content = file.read()
        return AkimboConfig.build(yaml.load(yaml_content, Loader=yaml.SafeLoader))


if __name__ == "__main__":
    config = deserialize_config("config.yaml")
    print(config)
