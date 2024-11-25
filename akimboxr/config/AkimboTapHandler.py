import asyncio
from threading import Timer
from typing import Callable


class AkimboTapHandler:
    def __init__(self, single: Callable[[], None], double: Callable[[], None],
                 triple: Callable[[], None], loop: asyncio.AbstractEventLoop, timeout: float, code: int):
        self.__single = single
        self.__double = double
        self.__triple = triple
        self.__loop = loop
        self.__timeout = timeout
        self.__task = None
        self.__last_presses = []
        self.__code = code

    def __cancel(self):
        print("Cancelled")
        if self.__task is not None:
            self.__task.cancel()
            self.__task = None

    def __presses(self):
        return len(self.__last_presses)

    def execute(self):
        print("Executing")

        now = self.__loop.time()

        self.__last_presses.append(now)
        self.__last_presses = list(
            filter(lambda x: now - x < self.__timeout, self.__last_presses)
        )

        print(f"{len(self.__last_presses)} presses in {self.__timeout} seconds")

        can_run_single_immediate = self.__single is not None and self.__double is None and self.__triple is None
        can_run_double_immediate = self.__double is not None and self.__triple is None
        can_run_triple_immediate = self.__triple is not None
        needs_rerun_single = self.__single is not None and self.__double is None and self.__triple is not None

        if self.__presses() == 1:
            print("1 press")
            if can_run_single_immediate:
                print("Single immediate")
                self.__last_presses = []
                self.__single()
            elif self.__single is not None:
                print(f"Single defer ({self.__timeout}s)")
                self.__task = asyncio.get_event_loop().call_later(self.__timeout, self.__single, )
            else:
                print("Single noop")

        if self.__presses() == 2:
            print("2 presses")
            self.__cancel()
            if needs_rerun_single:
                print(f"Rerun single defer ({self.__timeout}s)")
                self.__task = self.__loop.call_later(self.__timeout, self.__single_twice, )
            elif can_run_double_immediate:
                print("Double immediate")
                self.__last_presses = []
                self.__double()
            elif self.__double is not None:
                print(f"Double defer ({self.__timeout}s)")
                self.__task = self.__loop.call_later(self.__timeout, self.__double, )
            else:
                print("Double noop")

        if self.__presses() == 3:
            print("3 presses")
            self.__cancel()
            if can_run_triple_immediate:
                self.__triple()
                self.__last_presses = []
            else:
                print("Triple noop")

    def __single_twice(self):
        self.__single()
        self.__single()

    def __repr__(self):
        return f"""AkimboTapHandler({self.__code}{" x1" if self.__single else ""}{" x2" if self.__double else ""}{" x3" if self.__triple else ""})"""
