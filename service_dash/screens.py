from textual import events, on
from textual.app import ComposeResult
from textual.containers import Center, HorizontalGroup, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.validation import Function
from textual.widgets import Button, Input, Label, ListItem, Placeholder, Static

from components.dashboard import (
    ClusterList,
    ServiceActivity,
    ServiceDetail,
    LeftHandSide,
)
from components.footer import FooterComponent
from components.header import HeaderComponent
from messages import RedeployRequested
from repository.service import list_clusters


class DashboardScreen(Screen):

    content = reactive("Select a cluster or service to begin")

    def compose(self) -> ComposeResult:
        self.left_hand_side = LeftHandSide()
        self.service_detail = ServiceDetail()
        self.service_activity = ServiceActivity()
        self.id = "DASHBOARD"
        yield HeaderComponent()
        with HorizontalGroup() as hg:
            hg.styles.height = "100%"
            yield self.left_hand_side
            with Vertical():
                yield self.service_detail
                yield self.service_activity
        yield FooterComponent()


class ClusterSelectorScreen(ModalScreen):
    CSS_PATH = "styles/cluster_selector.tcss"
    clusters = list_clusters()

    def on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        self.id = "SELECT_CLUSTER"
        list_items = (
            ListItem(Label(k), name=v, id=k) for k, v in self.clusters.items()
        )
        yield VerticalGroup(
            Label("Select Cluster"),
            ClusterList(*list_items),
            id="select_cluster",
        )


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Placeholder("Help Screen")
        yield FooterComponent()


class ExitConfirmScreen(ModalScreen):
    CSS_PATH = "styles/exit_confirm_screen.tcss"

    def on_key(self, event: events.Key):
        if event.name == "escape":
            self.app.pop_screen()
        elif event.name == "enter":
            self.app.exit()

    def compose(self) -> ComposeResult:
        vertical_group = VerticalGroup(
            Center(
                Static("This will exit the application"),
                Button.error("OK", id="exit_confirm_button"),
            ),
            id="exit_confirm",
        )
        vertical_group.border_title = "Confirm Exit"
        yield vertical_group


class RedeployServiceScreen(ModalScreen):
    CSS_PATH = "styles/redeploy_service.tcss"

    def on_key(self, event: events.Key):
        if event.name == "escape":
            self.app.pop_screen()

    @on(Input.Submitted)
    def redeploy_service(self):
        input = self.query_one(Input)
        if input.is_valid:
            self.post_message(
                RedeployRequested(self.app.selected_cluster, self.app.selected_service)
            )
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        vertical_group = VerticalGroup(
            Input(
                placeholder="Type Yes",
                type="text",
                validators=[Function(is_yes, "You must type in 'yes'")],
                id="confirm_input",
            ),
            id="redeploy_screen",
        )
        vertical_group.border_title = "Confirm Redeploy"
        yield vertical_group


def is_yes(value: str) -> bool:
    return value.upper() == "YES"
