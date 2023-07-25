# A flexible and fast Minecraft server software written completely in Python.
# Copyright (C) 2021 PyMine

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import concurrent.futures
import asyncio
import sys
import os


print('Avviato')

if not sys.implementation.version[:3] >= (3, 7, 9):  # Ensure user is on correct version of Python
    print("You are not on a supported version of Python. Please update to version 3.7.9 or later.")
    exit(1)

try:
    import git
except ModuleNotFoundError:
    print(
        "You need to install PyMine's dependencies, either use poetry or use the requirements.txt file."
    )
    exit(1)
except BaseException:
    print(
        "PyMine requires git to be installed, you can download it here: https://git-scm.com/downloads."
    )
    exit(1)

# try:
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# except BaseException:
#     uvloop = None

# ensure the pymine modules are accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ensure the current working directory is correct
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from pymine.api.errors import ServerBindingError
from pymine.api.console import Console
import pymine.server


async def main():
    console = Console()

    # if uvloop:
    #     console.debug("Using uvloop as the asyncio event loop.")

    asyncio.get_event_loop().set_exception_handler(console.task_exception_handler)

    process_executor = concurrent.futures.ProcessPoolExecutor()
    thread_executor = concurrent.futures.ThreadPoolExecutor()

    server = pymine.server.Server(console, process_executor, thread_executor)
    pymine.server.server = server

    try:
        await server.start()
    except ServerBindingError as e:
        console.error(e.msg)
    except BaseException as e:
        console.critical(console.f_traceback(e))

    try:
        await server.stop()
    except BaseException as e:
        console.critical(console.f_traceback(e))

    process_executor.shutdown(wait=False)
    thread_executor.shutdown(wait=False)

    if (
        os.name == "posix"
    ):  # for some reason prompt_toolkit causes issues after exiting PyMine sometimes, this fixes those.
        os.system("stty sane")

    exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as e:
        os._exit(e.code)
