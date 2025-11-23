import os
import sys
import socket

class ANSI:
    ESC, BOLD, DIM, ITALIC, UNDERLINE, BLINK, REVERSE, HIDDEN = [""] * 8
    RESET, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [""] * 9

def ansi_check():
    if not sys.stdout.isatty():
        return False

    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32

        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()

        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False

        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if kernel32.SetConsoleMode(handle, new_mode) == 0:
            return False

        return True

    term = os.environ.get("TERM", "")
    if term in ("", "dumb"):
        return False

    return True

def get_free_port(host=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

if ansi_check():
    ANSI.ESC = "\x1b["
    ANSI.RESET = ANSI.ESC + "0m"

    ANSI.BOLD = ANSI.ESC + "1m"
    ANSI.DIM = ANSI.ESC + "2m"
    ANSI.ITALIC = ANSI.ESC + "3m"
    ANSI.UNDERLINE = ANSI.ESC + "4m"
    ANSI.BLINK = ANSI.ESC + "5m"
    ANSI.REVERSE = ANSI.ESC + "7m"
    ANSI.HIDDEN = ANSI.ESC + "8m"

    ANSI.BLACK = ANSI.ESC + "30m"
    ANSI.RED = ANSI.ESC + "31m"
    ANSI.GREEN = ANSI.ESC + "32m"
    ANSI.YELLOW = ANSI.ESC + "33m"
    ANSI.BLUE = ANSI.ESC + "34m"
    ANSI.MAGENTA = ANSI.ESC + "35m"
    ANSI.CYAN = ANSI.ESC + "36m"
    ANSI.WHITE = ANSI.ESC + "37m"
