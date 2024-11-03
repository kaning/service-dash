from typing import Dict

from textual.app import ComposeResult
from textual.containers import Container, VerticalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, RichLog, Rule, Static


class ClusterName(Static):
    cluster_name = reactive("Cluster: <Select Cluster>")
    cluster_arn = reactive("ARN: Cluster_ARN")

    def on_mount(self):
        self.update(self.cluster_name)

    def update_name(self, new_name):
        self.cluster_name = new_name
        self.update(f"Cluster: {self.cluster_name}")

    def update_arn(self, arn):
        self.cluster_arn = arn

    def get_arn(self):
        return self.cluster_arn


class ServiceName(Static):
    service_name = reactive("Service: <Select Service>")
    service_arn = reactive("ARN: <Select service>")

    def on_mount(self):
        self.update(self.service_name)

    def update_name(self, new_name):
        self.service_name = new_name
        self.update(f"Service: {self.service_name}")

    def update_arn(self, arn):
        self.service_arn = arn

    def get_arn(self):
        return self.service_arn


class ServiceList(ListView):

    def update_list(self, services: Dict):
        self.clear()
        for name, arn in services.items():
            self.append(ListItem(Label(name), id=name, name=arn))


class ServiceListWrapper(VerticalScroll):
    def compose(self) -> ComposeResult:
        self.styles.border = ("solid", "green")
        self.border_title = "[1] Service List"
        yield VerticalScroll(ServiceList(id="service_list"))


class ClusterList(ListView):
    def on_mount(self):
        self.focus(True)


class LeftHandSide(Container):
    def compose(self) -> ComposeResult:
        self.styles.border = ("solid", "green")
        self.styles.width = 50
        self.styles.height = "100%"
        self.line = Rule()
        self.line.styles.color = "green"
        yield ClusterName()
        yield ServiceName()
        yield self.line
        yield ServiceListWrapper()


class ServiceDetail(Container):
    def compose(self) -> ComposeResult:
        self.styles.border = ("solid", "green")
        self.styles.height = "60%"
        self.border_title = "Service Details"
        self.rich_log = RichLog(highlight=True, markup=True, id="detail_pane")
        yield self.rich_log


class ServiceActivity(Container):
    def compose(self) -> ComposeResult:
        self.styles.border = ("solid", "yellow")
        self.styles.height = "40%"
        self.border_title = "Service Activity"
        self.rich_log = RichLog(
            highlight=True, markup=True, wrap=True, id="service_activity_pane"
        )
        yield self.rich_log
