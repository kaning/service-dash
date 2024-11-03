from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer


class FooterComponent(Footer):
    CSS_PATH = "styles/footer.tcss"

    def on_mount(self) -> None:
        self.show_command_palette = False
