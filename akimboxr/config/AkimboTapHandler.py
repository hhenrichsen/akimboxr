import asyncio
from datetime import datetime, timedelta
from threading import Timer
from typing import Callable


class AkimboTapHandler:
    def __init__(
            self,
            single: Callable[[...], Callable[[], None]],
            double: Callable[[...], Callable[[], None]],
            triple: Callable[[...], Callable[[], None]],
            timeout: float,
            code: int):
        self.__single = single
        self.__double = double
        self.__triple = triple
        self.__timeout = timeout
        self.__task = None
        self.__last_presses = []
        self.__code = code

    def __cancel(self):
        if self.__task is not None:
            self.__task()
            self.__task = None

    def __presses(self):
        return len(self.__last_presses)

    def execute(self, layers):
        now = datetime.now()
        self.__last_presses.append(now)
        self.__last_presses = list(
            filter(lambda press: now - press < timedelta(seconds=self.__timeout), self.__last_presses)
        )

        can_run_single_immediate = self.__single is not None and self.__double is None and self.__triple is None
        can_run_double_immediate = self.__double is not None and self.__triple is None
        can_run_triple_immediate = self.__triple is not None
        needs_rerun_single = self.__single is not None and self.__double is None and self.__triple is not None

        if self.__presses() == 1:
            if can_run_single_immediate:
                self.__last_presses = []
                self.__single(layers=layers)
            elif self.__single is not None:
                self.__task = self.__single(layers=layers, delay=self.__timeout)
            else:
                # noop
                pass

        if self.__presses() == 2:
            self.__cancel()
            if needs_rerun_single:
                self.__single_twice(layers=layers)
            elif can_run_double_immediate:
                self.__last_presses = []
                self.__double(layers=layers)
            elif self.__double is not None:
                self.__double(layers=layers, delay=self.__timeout)
            else:
                # noop
                pass

        if self.__presses() == 3:
            self.__cancel()
            if can_run_triple_immediate:
                self.__triple(layers=layers)
                self.__last_presses = []
            else:
                # noop
                pass

    def __single_twice(self, *args, **kwargs):
        self.__single(*args, **kwargs)
        self.__single(*args, **kwargs)

    def __repr__(self):
        return f"""AkimboTapHandler({self.__code}{" x1" if self.__single else ""}{" x2" if self.__double else ""}{" x3" if self.__triple else ""})"""
