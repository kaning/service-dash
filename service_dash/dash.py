from datetime import datetime
from textual import work
from textual.app import App
from textual.widgets import ListView
from textual.worker import NoActiveWorker, get_current_worker
from repository.service import (
    describe_service,
    extract_log_group_name,
    list_services,
    redeploy_service,
    log_client,
)
from messages import RedeployRequested
from components.dashboard import ClusterName, ServiceList, ServiceName
from screens import (
    ClusterSelectorScreen,
    DashboardScreen,
    ExitConfirmScreen,
    RedeployServiceScreen,
)
from components.dashboard import ClusterList


class ServiceDashApp(App):
    """A Textual app to manage stopwatches."""

    BINDING_GROUP_TITLE = "Actions"

    BINDINGS = [
        ("c", "select_cluster", "Select Cluster"),
        ("l", "service_logs", "Tail Service Logs"),
        ("x", "exit", "Exit Service Dash"),
        ("h", "help", "Show help screen"),
        ("s", "pane_one", "Select Service"),
        ("ctrl+r", "redeploy_service", "Redeploy Service"),
    ]

    SCREENS = {
        "select_cluster_screen": ClusterSelectorScreen,
        "dashboard": DashboardScreen,
        "exit_confirm": ExitConfirmScreen,
        "redeploy_service": RedeployServiceScreen,
    }

    MODES = {"dashboard": DashboardScreen}

    selected_service = None
    selected_cluster = None
    tailing_logs = None

    def action_select_cluster(self):
        self.push_screen("select_cluster_screen")

    def action_pane_one(self):
        if self.screen.id == "DASHBOARD":
            pane_one = self.query_one(ServiceList)
            pane_one.focus(True)

    async def action_service_logs(self):
        if self.selected_service:
            self.get_service_logs(self.selected_service)

    @work(exclusive=True, thread=True)
    def get_service_logs(self, service):
        log_group = extract_log_group_name(service)
        activity_pane = self.query_one("#service_activity_pane")
        activity_pane.write(f"Getting logs for {service}")
        worker = get_current_worker()
        self.tailing_logs = service
        activity_pane.write(f"TAILING FOR {self.tailing_logs}")
        activity_pane.write(f"SELECTED SERVICE {self.selected_service}")
        try:
            response = log_client.start_live_tail(
                logGroupIdentifiers=[
                    f"arn:aws:logs:eu-west-1:358238661734:log-group:{log_group}"
                ],
            )
            event_stream = response["responseStream"]
            # Handle the events streamed back in the response
            for event in event_stream:
                if self.tailing_logs != self.selected_service:
                    activity_pane.clear()
                    worker.cancel()
                    break
                # Handle when session is started
                if "sessionStart" in event:
                    session_start_event = event["sessionStart"]
                    activity_pane.write(session_start_event)
                # Handle when log event is given in a session update
                elif "sessionUpdate" in event:
                    log_events = event["sessionUpdate"]["sessionResults"]
                    for log_event in log_events:
                        if not worker.is_cancelled:
                            activity_pane.write(
                                "[{date}] {log}".format(
                                    date=datetime.fromtimestamp(
                                        log_event["timestamp"] / 1000
                                    ),
                                    log=log_event["message"],
                                )
                            )
                        else:
                            event_stream.close()
                            break
                else:
                    # On-stream exceptions are captured here
                    raise RuntimeError(str(event))
        except Exception as e:
            activity_pane.write(e)

    def action_redeploy_service(self):
        if self.selected_service:
            self.push_screen("redeploy_service")

    def action_exit(self):
        if self.screen.id == "DASHBOARD":
            self.push_screen("exit_confirm")
        else:
            self.pop_screen()

    def on_redeploy_requested(self, message: RedeployRequested):
        log = self.query_one("#service_activity_pane")
        log.clear()
        response = redeploy_service(message.cluster, message.service)
        log.write(response)

    def on_list_view_selected(self, message: ListView.Selected):
        if self.screen.id == "DASHBOARD":
            if isinstance(message.control, ServiceList):
                service_name = self.query_one(ServiceName)
                service_name.update_name(message.item.id)
                cluster_name = self.query_one(ClusterName)
                self.selected_service = message.item.id

                detail_pane = self.query_one("#detail_pane")
                detail_pane.clear()
                detail_pane.write(
                    describe_service(
                        cluster_arn=cluster_name.cluster_name,
                        service_arn=message.item.name,
                    )
                )
                detail_pane.scroll_to(y=0)
                detail_pane.focus(True)

                activity_pane = self.query_one("#service_activity_pane")
                activity_pane.clear()
                try:
                    get_current_worker().cancel()
                except NoActiveWorker as e:
                    pass

        if self.screen.id == "SELECT_CLUSTER":
            self.app.pop_screen()
            if isinstance(message.control, ClusterList):
                cluster_name = self.query_one(ClusterName)
                cluster_name.update_name(message.item.id)
                cluster_name.update_arn(message.item.name)
                self.selected_cluster = message.item.name
                service_list = self.query_one(ServiceList)
                services = list_services(message.item.name)
                service_list.update_list(services)
                service_list.focus(True)

    def on_mount(self):
        self.switch_mode("dashboard")
