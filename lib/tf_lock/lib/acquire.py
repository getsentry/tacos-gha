#!/usr/bin/env python3.12
from __future__ import annotations

import asyncio
from os import getenv

Command = tuple[str, ...]
ExitCode = str | int

TF_SLEEP = 10  # terraform has a ten-second sleep loop
EOF = b""
DEBUG: int = int(getenv("DEBUG") or "0")

if DEBUG >= 3:
    TIMEOUT = 1
    TERRAFORM: Command = (
        "sh",
        "-exc",
        """\
printf "> "
read -r line
echo line: "$line"
""",
    )
else:
    TIMEOUT = 1 * TF_SLEEP + 1
TERRAFORM = ("terraform", "console")


def debug(*msg: object) -> None:
    if DEBUG:
        from sys import stderr

        print("+ :", *msg, file=stderr, flush=True)


def ansi_denoise(ansi_text: bytes) -> bytes:
    import re

    csi = b"\033["  # ]  auto-indenter is stupid =.=
    control_re = re.escape(csi) + b"[^A-Za-z]*[A-Za-z]"
    backspace_re = b".\b"
    noise_re = re.compile(b"|".join((backspace_re, control_re)))
    return noise_re.sub(b"", ansi_text)


async def get_prompt(output: asyncio.StreamReader) -> str:
    while not output.at_eof():
        try:
            data = await output.read(128)
        except OSError as error:
            if error.errno == 5:  # input/output error, i.e. a broken pipe
                break
            else:
                raise
        prompt = ansi_denoise(data)
        if prompt:
            return prompt.decode("UTF-8")
    return ""


async def run_terraform(
    cmd: Command,
) -> tuple[asyncio.subprocess.Process, asyncio.StreamReader]:
    import os

    parent, child = os.openpty()

    import tty

    tty.setraw(parent)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=child,
        stdin=child,
        # this is required to ensure that terraform console is killed without cleanup
        # this ensures the lock isn't dropped
        start_new_session=True,
    )
    os.close(child)

    loop = asyncio.get_running_loop()
    output = asyncio.StreamReader(loop=loop)

    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(output, loop=loop),
        os.fdopen(parent, "rb", buffering=0),
    )
    return proc, output


async def acquire() -> ExitCode:
    import os
    import signal

    proc, output = await run_terraform(TERRAFORM)
    wait = asyncio.create_task(proc.wait())
    timer = asyncio.create_task(asyncio.sleep(TIMEOUT))

    while True:
        prompt = asyncio.create_task(get_prompt(output))
        await asyncio.wait(
            [wait, prompt, timer], return_when=asyncio.FIRST_COMPLETED
        )
        if wait.done():
            returncode = wait.result()
            return f"terraform exitted early, code {returncode}"
        elif timer.done() or not prompt.done():
            # use negative process id because we want to kill the process group
            os.kill(-proc.pid, signal.SIGKILL)
            return f"timeout (seconds): {TIMEOUT}"
        elif (result := prompt.result()).endswith("> "):
            debug("got prompt, exit un-gracefully")
            assert not wait.done(), wait
            os.kill(-proc.pid, signal.SIGKILL)
            debug("terraform exitted, code", await proc.wait())
            return 0
        else:
            debug(f"unexpected output: {repr(result)}")


def main() -> ExitCode:
    import logging

    logging.basicConfig(level=logging.DEBUG if DEBUG >= 2 else logging.INFO)
    return asyncio.run(acquire(), debug=DEBUG > 0)


if __name__ == "__main__":
    raise SystemExit(main())
