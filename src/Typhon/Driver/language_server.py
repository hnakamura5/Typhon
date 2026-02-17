from ..LanguageServer import server
from ..Driver.debugging import (
    debug_file_write,
    debug_verbose_print,
    is_debug_mode,
    BinaryIOLogger,
    is_debug_verbose,
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
    if is_debug_verbose():
        debug_setup_logging(verbose=is_debug_verbose())
    server.start_io(
        stdin=BinaryIOLogger(sys.stdin.buffer),
        stdout=BinaryIOLogger(sys.stdout.buffer),
    )

    # TODO: Support TCP Mode?
    # server.start_tcp("127.0.0.1", 8080)
