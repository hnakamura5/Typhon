from ..LanguageServer import server
from ..Driver.debugging import (
    is_debug_mode,
    BinaryIOLogger,
    set_debug_log_file,
    debug_print,
    get_debug_log_file,
)
import sys
import logging


def language_server():
    """
    Start the Typhon Language Server.
    """
    if (log_file := get_debug_log_file()) is not None:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            filemode="a",
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )

    server.start_io(
        stdin=BinaryIOLogger(sys.stdin.buffer),
        stdout=BinaryIOLogger(sys.stdout.buffer),
    )

    # TODO: Support TCP Mode?
    # server.start_tcp("127.0.0.1", 8080)
