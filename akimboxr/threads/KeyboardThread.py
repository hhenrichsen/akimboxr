from enum import Enum
from queue import Queue, Empty
from threading import Thread
from typing import Dict, List

from pynput.keyboard import KeyCode, Key, Controller
from datetime import datetime, timedelta
from time import sleep
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel('INFO')

queue = Queue()
_controller = Controller()


class KeyOperation(Enum):
    Press = "press",
    Release = "release",
    Tap = "tap",
    Cancel = "cancel"


class KeyboardThreadSupplier:
    def __init__(self, _queue: Queue):
        self.queue = _queue
        self._task_id = 0

    def _next_task_id(self):
        task_id = self._task_id
        self._task_id += 1
        return task_id

    def _cancel_key(self, task_id: int):
        logger.debug(f"Pushing cancel for {task_id}")
        self.queue.put((task_id, KeyOperation.Cancel))
        logger.debug(f"Queue size {self.queue.qsize()}")

    def press_key(self, key: Key | KeyCode, delay: float = 0):
        logger.debug(f"Pushing press for {key}")
        task_id = self._next_task_id()
        self.queue.put((task_id, KeyOperation.Press, key, delay))
        logger.debug(f"Queue size {self.queue.qsize()}")
        return lambda: self._cancel_key(task_id)

    def release_key(self, key: Key | KeyCode, delay: float = 0):
        logger.debug(f"Pushing release for {key}")
        task_id = self._next_task_id()
        self.queue.put((task_id, KeyOperation.Release, key, delay))
        logger.debug(f"Queue size {self.queue.qsize()}")
        return lambda: self._cancel_key(task_id)

    def tap_key(self, key: Key | KeyCode, delay: float = 0):
        logger.debug(f"Pushing tap for {key}")
        task_id = self._next_task_id()
        self.queue.put((task_id, KeyOperation.Tap, key, delay))
        logger.debug(f"Queue size {self.queue.qsize()}")
        return lambda: self._cancel_key(task_id)


def _worker(key_queue: Queue):
    tasks: Dict[int, (datetime, KeyOperation, Key | KeyCode)] = {}
    times: Dict[datetime, List[int]] = {}

    def _del_task(to_delete):
        if to_delete not in tasks:
            return
        time, _, _ = tasks[to_delete]
        times[time].remove(to_delete)
        del tasks[to_delete]

    while True:
        logger.debug("Poll")
        now = datetime.now()

        for entry in times:
            if entry < now:
                for task_id in sorted(times[entry]):
                    logger.debug(f"Running deferred task {task_id}")
                    _, mode, key = tasks[task_id]
                    match mode:
                        case KeyOperation.Press:
                            logger.info(f"Pressing {key}")
                            _controller.press(key)

                        case KeyOperation.Release:
                            logger.info(f"Releasing {key}")
                            _controller.release(key)

                        case KeyOperation.Tap:
                            logger.info(f"Tapping {key}")
                            _controller.tap(key)
                    _del_task(task_id)

        times = dict(filter(lambda x: len(x[1]) > 0, times.items()))

        logger.debug(f"Queue length {key_queue.qsize()}")

        try:
            task_id, mode, *rest = key_queue.get(block=False)
            logger.debug(f"Got {mode} ({task_id}) from queue")
            match mode:
                case KeyOperation.Cancel:
                    _del_task(task_id)

                case KeyOperation.Press:
                    key, delay = rest
                    if delay > 0:
                        tasks[task_id] = (now + timedelta(seconds=delay), mode, key)
                        times[now + timedelta(seconds=delay)] = times.get(now + timedelta(seconds=delay), []) + [
                            task_id]
                    else:
                        logger.info(f"Pressing {key}")
                        _controller.press(key)
                        _del_task(task_id)

                case KeyOperation.Release:
                    key, delay = rest
                    if delay > 0:
                        tasks[task_id] = (now + timedelta(seconds=delay), mode, key)
                        times[now + timedelta(seconds=delay)] = times.get(now + timedelta(seconds=delay), []) + [
                            task_id]
                    else:
                        logger.info(f"Releasing {key}")
                        _controller.release(key)
                        _del_task(task_id)

                case KeyOperation.Tap:
                    key, delay = rest
                    if delay > 0:
                        tasks[task_id] = (now + timedelta(seconds=delay), mode, key)
                        times[now + timedelta(seconds=delay)] = times.get(now + timedelta(seconds=delay), []) + [
                            task_id]
                    else:
                        logger.info(f"Tapping {key}")
                        _controller.tap(key)
                        _del_task(task_id)
            key_queue.task_done()
        except Empty:
            pass
        sleep(0)


def run_keyboard_thread():
    worker = Thread(target=_worker, daemon=True, args=(queue,))
    worker.start()
    logger.info("Started keyboard worker")
