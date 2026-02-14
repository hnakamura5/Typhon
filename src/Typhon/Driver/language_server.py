from ..LanguageServer import server
from ..Driver.debugging import (
    is_debug_mode,
    BinaryIOLogger,
    set_debug_log_file,
    debug_print,
    get_debug_log_file,
    set_debug_verbose,
    debug_setup_logging,
)
import sys
import logging


def language_server():
    """
    Start the Typhon Language Server.
    """
    debug_setup_logging()
    server.start_io(
        stdin=BinaryIOLogger(sys.stdin.buffer),
        stdout=BinaryIOLogger(sys.stdout.buffer),
    )

    # TODO: Support TCP Mode?
    # server.start_tcp("127.0.0.1", 8080)
