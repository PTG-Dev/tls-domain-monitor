# =============================================================================
# main.py — Entry point / CLI menu (the boss of bad decisions)
#
# Displays the main interactive menu and sends the user
# to wherever they think they know what they're doing:
#
#   1. Quick Scan        → real-time domain discovery via CT logs
#   2. Advanced Options  → coming soon (probably)
#   3. Exit              → graceful escape
# =============================================================================

import logging
import sys

__version__ = "1.0.1"

from boot_screen   import show_boot_screen
from quick_scan    import QuickScan
from advanced_scan import AdvancedScan
from scan_params   import ScanParams

_M  = "\033[38;5;183m"   # pale mauve
_R  = "\033[0m"           # reset

logging.basicConfig(
    level   = logging.INFO,
    format  = "[%(levelname)s] %(message)s",
)


# ─────────────────────────────────────────────────────────────────────────────
# Banner — ASCII art header displayed at launch
#
# Because who doesn't love staring at their own beautiful banner?
# Shows up when the program starts to flex a little personality.
# ─────────────────────────────────────────────────────────────────────────────




# ─────────────────────────────────────────────────────────────────────────────
# Menu — CLI menu display and navigation (guides users or silently judges them)
# ─────────────────────────────────────────────────────────────────────────────

class Menu:
    """
    Handles the main CLI menu loop.

    Displays options, reads user input, and delegates to the
    appropriate module based on the selection.
    """

    def __init__(self):
        # Instantiate the modules available from the menu
        self.quick_scan  = QuickScan()
        self._show_menu  = True

    # ── Display helpers ───────────────────────────────────────────────────────

    def _print_banner(self) -> None:
        """Prints the ASCII banner at program startup."""
        show_boot_screen()

    def _print_menu(self) -> None:
        """Prints the main menu options."""
        _B  = "\033[1m"
        _DI = "\033[2m"
        _W  = "\033[38;5;255m"
        _D  = "\033[38;5;141m"
        sep = f"  {_DI}  {'─'*36}{_R}"
        print(
            f"\n"
            f"     {_W}{_B}C E R T   M O N I T O R{_R}\n"
            f"\n"
            f"{sep}\n"
            f"     {_D}[{_W}{_B} 1 {_R}{_D}]{_R}  {_M}Quick Scan{_R}\n"
            f"     {_DI}Live CT log  ·  real-time domains{_R}\n"
            f"{sep}\n"
            f"     {_D}[{_W}{_B} 2 {_R}{_D}]{_R}  {_M}Help{_R}\n"
            f"     {_DI}scan commands & flags{_R}\n"
            f"{sep}\n"
            f"     {_D}[{_W}{_B} 3 {_R}{_D}]{_R}  {_M}Exit{_R}\n"
            f"{sep}\n"
        )

    def _print_help(self) -> None:
        """Prints the scan command reference."""
        _B  = "\033[1m"
        _DI = "\033[2m"
        _W  = "\033[38;5;255m"
        _D  = "\033[38;5;141m"
        sep = f"  {_DI}  {'─'*44}{_R}"
        print(
            f"\n"
            f"     {_W}{_B}C O M M A N D S{_R}\n"
            f"\n"
            f"{sep}\n"
            f"     {_M}scan{_R}  {_DI}[flags ...]{_R}\n"
            f"{sep}\n"
            f"     {_D}-k{_R}  {_W}keyword{_R}     {_DI}Filter — only show matching domains{_R}\n"
            f"     {_DI}ex:{_R}  scan -k bank\n"
            f"\n"
            f"     {_D}-l{_R}  {_W}limit{_R}       {_DI}Stop after N unique domains{_R}\n"
            f"     {_DI}ex:{_R}  scan -l 20\n"
            f"\n"
            f"     {_D}-r{_R}  {_W}http status{_R}  {_DI}Show HTTP response code per domain{_R}\n"
            f"     {_DI}ex:{_R}  scan -r\n"
            f"\n"
            f"     {_DI}combine:{_R}  scan -k bird -l 10 -r\n"
            f"{sep}\n"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _flush_input() -> None:
        """Drains buffered keypresses after a scan to prevent ghost inputs."""
        try:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except ImportError:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()

    # ── Input handler ─────────────────────────────────────────────────────────

    def _get_choice(self) -> str:
        """
        Prompts the user for a menu selection or a scan command.
        Returns the raw input string (stripped of whitespace).
        """
        try:
            return input(f"  {_M}┌─ Choice ──▶{_R}  ").strip()

        except (EOFError, KeyboardInterrupt):
            # CTRL+C or EOF during input → treat as exit
            return "3"

    # ── Router ────────────────────────────────────────────────────────────────

    def _route(self, choice: str) -> bool:
        """
        Routes the user's input to the correct action.
        Returns False when the program should exit, True to continue looping.
        """
        print()

        match choice:

            case "1":
                self.quick_scan.run()

                self._flush_input()
                print()
                return True

            case "2":
                self._print_help()
                
                #dont pop for nothing
                self._show_menu = False
                return True

            case _ if choice.lower().startswith("scan"):
                params = ScanParams.from_string(choice)
                if params is None:
                    print("  [!] Invalid scan command.")
                    print(f"  {_M}Usage:{_R}  scan [-k keyword] [-l limit] [-r]")
                    print()
                    return True
                AdvancedScan(params).run()
                self._flush_input()
                print()
                return True

            case "3":
                print("  Goodbye.")
                print()
                return False

            case _:
                
                print("  [!] Invalid choice. Enter 1, 2, 3, or  scan [-k keyword] [-l limit] [-r]")
                print()
                return True

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Starts the interactive CLI loop.
        Displays the banner once, then loops the menu until the user exits.
        """
        self._print_banner()

        running = True

        while running:
            if self._show_menu:
                self._print_menu()
            self._show_menu = True
            choice  = self._get_choice()
            running = self._route(choice)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    try:
        menu = Menu()
        menu.run()

    except KeyboardInterrupt:
        #CTRL+C thing
        print("\n\n  Interrupted. Exiting.")

    finally:
        # Reset terminal color back to normal on exit
        sys.stdout.write("\033[0m")
        sys.stdout.flush()
        sys.exit(0)
