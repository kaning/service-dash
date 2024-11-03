from datetime import datetime
from re import split
import time
import boto3
from typing import Dict


ecs_client = boto3.client("ecs")
log_client = boto3.client("logs")


def get_name_from_arn(arn: str):
    arn_names = split(":", arn)
    item_names = split("/", arn_names[len(arn_names) - 1])
    return item_names[len(item_names) - 1]


def list_clusters() -> Dict:
    return {get_name_from_arn(k): k for k in ecs_client.list_clusters()["clusterArns"]}


def list_services(cluster_arn):
    return {
        get_name_from_arn(k): k
        for k in ecs_client.list_services(cluster=cluster_arn, maxResults=50)[
            "serviceArns"
        ]
    }


def format_deployment(deployment: Dict) -> Dict:
    dep = {}
    dep["status"] = deployment["status"]
    dep["rollout_state"] = deployment["rolloutState"]
    dep["rollout_state_reason"] = deployment["rolloutStateReason"]
    dep["running"] = deployment["runningCount"]
    dep["pending"] = deployment["pendingCount"]
    dep["desired"] = deployment["desiredCount"]
    dep["create_at"] = deployment["createdAt"]
    return dep


def describe_service(cluster_arn: str, service_arn: str):
    try:
        service_data = {}
        service_description = ecs_client.describe_services(
            cluster=cluster_arn, services=[service_arn]
        )["services"]

        service_data["ARN"] = service_description[0]["serviceArn"]
        service_data["name"] = service_description[0]["serviceName"]
        service_data["status"] = service_description[0]["status"]
        service_data["created_at"] = service_description[0]["createdAt"]
        service_data["task_definition"] = service_description[0]["taskDefinition"]
        service_data["desired_count"] = service_description[0]["desiredCount"]
        service_data["running_count"] = service_description[0]["runningCount"]
        service_data["pending_count"] = service_description[0]["pendingCount"]
        service_data["deployments"] = list(
            map(format_deployment, service_description[0]["deployments"])
        )
        return service_data

    except Exception as e:
        return {"error": e}


def redeploy_service(cluster_name: str, service_name: str) -> Dict:
    try:
        service_deployment_description = ecs_client.update_service(
            cluster=cluster_name, service=service_name, forceNewDeployment=True
        )["service"]
        dep = {}
        dep["deployments"] = list(
            map(format_deployment, service_deployment_description["deployments"])
        )
        return dep
    except Exception as e:
        return {"error": e}


def extract_log_group_name(service_name):
    name_parts = split("-", service_name)
    env = name_parts[len(name_parts) - 1]
    service_name = "-".join(name_parts[: len(name_parts) - 2])
    return f"/ecs/{service_name}-task-{env}"


def get_cloud_logs(log_group):
    start_time = time.time()
    try:
        response = log_client.start_live_tail(
            logGroupIdentifiers=[
                f"arn:aws:logs:eu-west-1:358238661734:log-group:{log_group}"
            ],
        )
        event_stream = response["responseStream"]
        # Handle the events streamed back in the response
        for event in event_stream:
            # Set a timeout to close the stream.
            # This will end the Live Tail session.
            # if time.time() - start_time >= 10:
            # event_stream.close()
            # break
            # Handle when session is started
            if "sessionStart" in event:
                session_start_event = event["sessionStart"]
                print(session_start_event)
            # Handle when log event is given in a session update
            elif "sessionUpdate" in event:
                log_events = event["sessionUpdate"]["sessionResults"]
                for log_event in log_events:
                    yield (
                        "[{date}] {log}".format(
                            date=datetime.fromtimestamp(log_event["timestamp"] / 1000),
                            log=log_event["message"],
                        )
                    )
            else:
                # On-stream exceptions are captured here
                raise RuntimeError(str(event))
    except Exception as e:
        print(e)
