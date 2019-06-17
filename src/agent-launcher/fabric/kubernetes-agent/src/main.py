#
# SPDX-License-Identifier: Apache-2.0
#
import os
import zipfile
from utils import download_file, KubernetesClient
from network import FabricNetwork

AGENT_URL = os.getenv("AGENT_URL")
DEPLOY_NAME = os.getenv("DEPLOY_NAME")
NETWORK_TYPE = os.getenv("NETWORK_TYPE")
NETWORK_VERSION = os.getenv("NETWORK_VERSION")
NODE_TYPE = os.getenv("NODE_TYPE")
AGENT_CONFIG_FILE = os.getenv("AGENT_CONFIG_FILE")
AGENT_ID = os.getenv("AGENT_ID")
NODE_ID = os.getenv("NODE_ID")
OPERATION = os.getenv("OPERATION")

if __name__ == "__main__":
    config_file = download_file(AGENT_CONFIG_FILE, "/tmp")
    ext = os.path.splitext(config_file)[-1].lower()

    if ext == ".zip":
        with zipfile.ZipFile(config_file, "r") as zip_ref:
            zip_ref.extractall("/app")

    k8s_config = "/app/.kube/config"

    k8s_client = KubernetesClient(config_file=k8s_config)
    k8s_client.get_or_create_namespace(name=AGENT_ID)
    network = FabricNetwork(
        version=NETWORK_VERSION,
        node_type=NODE_TYPE,
        agent_id=AGENT_ID,
        node_id=NODE_ID,
    )
    config = network.generate_config()

    deployment = config.get("deployment")
    service = config.get("service")
    ingress = config.get("ingress")

    if OPERATION == "start":
        if deployment:
            k8s_client.create_deployment(AGENT_ID, **deployment)
        if service:
            success, service_response = k8s_client.create_service(
                AGENT_ID, **service
            )
            if service.get("service_type") == "NodePort" and success:
                ports = service_response.spec.ports
                ports = [
                    {"external": port.node_port, "internal": port.port}
                    for port in ports
                ]
                # set_ports_mapping(self._node_id, ports, True)
        if ingress:
            k8s_client.create_ingress(AGENT_ID, **ingress)