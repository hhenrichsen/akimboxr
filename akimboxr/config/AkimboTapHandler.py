import asyncio


class AkimboTapHandler:
    def __init__(self, single, double, triple, loop: asyncio.AbstractEventLoop, timeout: float, code: int):
        self.__single = single
        self.__double = double
        self.__triple = triple
        self.__loop = loop
        self.__timeout = timeout
        self.__task = None
        self.__last_presses = []
        self.__code = code

        def noop(down_layer):
            down_layer()

        self.__inner_execute = noop
        # TODO someone please help me make this better
        if single is not None:
            if double is None:
                if triple is None:
                    # We don't need to worry about duplicated key presses, run immediately
                    def anon(down_layer):
                        print("Single action")
                        self.__single(down_layer)

                    self.__inner_execute = anon
                    return
                else:

                    def anon(down_layer):

                        if len(self.__last_presses) >= 3:
                            self.__cancel()
                            self.__last_presses = []
                            print("Triple action")
                            self.__triple(down_layer)
                            return
                        elif len(self.__last_presses) >= 2:
                            # 2 presses should extend the timeout but not run the action yet
                            self.__cancel()

                            def double_action(down_layer):
                                self.__single(down_layer)
                                self.__single(down_layer)

                            print("Single action (defer)")

                            self.__task = self.__loop.call_later(
                                self.__timeout, double_action, down_layer
                            )
                            return
                        else:
                            print("Single action (defer)")
                            self.__task = self.__loop.call_later(
                                self.__timeout, self.__single, down_layer
                            )
                            return

                    self.__inner_execute = anon
                    return

            elif double is not None:

                def anon(down_layer):
                    if len(self.__last_presses) >= 3 and triple is not None:
                        self.__cancel()
                        self.__last_presses = []
                        print("Triple action")
                        self.__triple(down_layer)
                        return

                    if len(self.__last_presses) >= 2:
                        self.__cancel()
                        if triple is None:
                            # We don't need to worry about duplicated keypresses, run immediately
                            print("Double action")
                            self.__double(down_layer)
                            self.__last_presses = []
                            return
                        else:
                            print("Double action (defer)")
                            self.__task = self.__loop.call_later(
                                self.__timeout, self.__double, down_layer
                            )
                            return
                    else:
                        print("Single action (defer)")
                        self.__task = self.__loop.call_later(
                            self.__timeout, self.__single, down_layer
                        )

                self.__inner_execute = anon
                return

            # First press is a noop
            elif single is None:
                if double is not None:
                    if triple is None:

                        def anon(down_layer):
                            if self.__presses() >= 2:
                                print("Double action")
                                self.__double(down_layer)
                                self.__last_presses = []

                        self.__inner_execute = anon
                        return
                    else:

                        def anon(down_layer):
                            if self.__presses() >= 2:
                                print("Double action (defer)")
                                self.__task = self.__loop.call_later(
                                    self.__timeout, self.__double, down_layer
                                )
                            elif self.__presses() >= 3:
                                self.__cancel()
                                print("Triple action")
                                self.__triple(down_layer)

                        self.__inner_execute = anon
                        return

    def __cancel(self):
        if self.__task is not None:
            self.__task.cancel()
            self.__task = None

    def __presses(self):
        return len(self.__last_presses)

    def execute(self, down_layer):
        print("Executing")

        now = self.__loop.time()

        self.__last_presses.append(now)
        self.__last_presses = list(
            filter(lambda x: now - x < self.__timeout, self.__last_presses)
        )

        print(f"{len(self.__last_presses)} presses in {self.__timeout} seconds")

        self.__inner_execute(down_layer)

    def __repr__(self):
        return f"""AkimboTapHandler({self.__code}{" x1" if self.__single else ""}{" x2" if self.__double else ""}{" x3" if self.__triple else ""})"""
