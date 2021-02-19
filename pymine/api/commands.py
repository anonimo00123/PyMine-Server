import importlib
import asyncio
import uuid
import os

from pymine.util.stop import stop

from pymine.api.abc import AbstractParser
from pymine.api.parsers import parsers


class CommandHandler:
    def __init__(self, server):
        self.server = server
        self.console = server.console
        self._commands = {}  # {name: (func, node)}

    # loads default built in commands
    @staticmethod
    def load_commands():  # only loads commands inside cmds folder, not subfolders
        for file in os.listdir("pymine/logic/cmds"):
            if file.endswith(".py"):
                importlib.import_module(f"pymine.logic.cmds.{file[:-3]}")

    def on_command(self, name: str, node: str):
        if name in self._commands:
            raise ValueError("Command name is already in use.")

        if " " in name:
            raise ValueError("Command name may not contain spaces.")

        def deco(func):
            if not asyncio.iscoroutinefunction(func):
                raise ValueError("Decorated object must be a coroutine function.")

            self._commands[name] = func, node
            return func

        return deco

    async def command(self, uuid_: uuid.UUID, full: str):
        split = full.split(" ")
        command = self._commands.get(split[0])
        args_text = " ".join(split[1:])

        if command is None:
            self.console.warn(f"Invalid/unknown command: {repr(split[0])}")
            return

        parsed_to = 0
        args = []

        for arg, parser in command.__annotations__.items()[1:]:  # [1:] to skip first arg which should be the uuid
            if not isinstance(parser, AbstractParser):
                raise ValueError(f"{parser} is not an instance of AbstractParser")

            parsed_to, parsed = parser.parse(args_text[parsed_to:])

            args.append(parsed)

        try:
            await command(uuid_, *args)
        except BaseException as e:
            self.console.error(f'Error while executing command {split[0]}: {self.console.f_traceback(e)}')

    async def handle_console(self):
        eoferr = False

        try:
            while True:
                in_ = await self.console.fetch_input()

                await self.server_command(in_)

                if command.startswith("stop"):
                    break

                await asyncio.sleep(0)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        except EOFError:
            eoferr = True
        except BaseException as e:
            self.console.error(self.console.f_traceback(e))

        if eoferr:
            await stop(self.server)
