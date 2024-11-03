from textual.message import Message


class ClusterSelected(Message):
    def __init__(self, msg: str) -> None:
        self.message = msg
        super().__init__()


class ServiceSelected(Message):
    def __init__(self, msg: str) -> None:
        self.message = msg
        super().__init__()


class RedeployRequested(Message):
    def __init__(self, cluster: str, service: str) -> None:
        self.service = service
        self.cluster = cluster
        super().__init__()
