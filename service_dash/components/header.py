from textual.widgets import Header


class HeaderComponent(Header):
    def __init__(
        self,
        show_clock: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        icon: str | None = None,
        time_format: str | None = None
    ):
        super().__init__(
            show_clock,
            id=id,
            classes=classes,
            icon=icon,
            time_format=time_format,
        )

        self.app.title = "SERVICE DASHBOARD"
