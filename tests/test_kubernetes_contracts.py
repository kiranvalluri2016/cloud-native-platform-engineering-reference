from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]


def render_overlay(environment: str) -> list[dict]:
    result = subprocess.run(
        ["kubectl", "kustomize", str(ROOT / "k8s" / "overlays" / environment)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [document for document in yaml.safe_load_all(result.stdout) if document]


def resource(documents: list[dict], kind: str, name: str) -> dict:
    return next(
        document
        for document in documents
        if document["kind"] == kind and document["metadata"]["name"] == name
    )


def test_dev_and_prod_render_with_isolated_namespaces_and_governance() -> None:
    dev = render_overlay("dev")
    prod = render_overlay("prod")
    dev_deployment = resource(dev, "Deployment", "platform-api")
    prod_deployment = resource(prod, "Deployment", "platform-api")
    dev_hpa = resource(dev, "HorizontalPodAutoscaler", "platform-api")
    prod_hpa = resource(prod, "HorizontalPodAutoscaler", "platform-api")

    assert dev_deployment["metadata"]["namespace"] == "platform-dev"
    assert prod_deployment["metadata"]["namespace"] == "platform-prod"
    assert dev_deployment["spec"]["replicas"] == dev_hpa["spec"]["minReplicas"] == 1
    assert prod_deployment["spec"]["replicas"] == prod_hpa["spec"]["minReplicas"] == 3
    assert dev_hpa["spec"]["maxReplicas"] == 2
    assert prod_hpa["spec"]["maxReplicas"] == 6
    assert ":latest" not in dev_deployment["spec"]["template"]["spec"]["containers"][0]["image"]
    assert "@sha256:" in prod_deployment["spec"]["template"]["spec"]["containers"][0]["image"]


def test_deployment_is_hardened_and_probes_target_pod_port() -> None:
    documents = render_overlay("prod")
    deployment = resource(documents, "Deployment", "platform-api")
    service_account = resource(documents, "ServiceAccount", "platform-api")
    hpa = resource(documents, "HorizontalPodAutoscaler", "platform-api")
    spec = deployment["spec"]
    pod_spec = spec["template"]["spec"]
    container = pod_spec["containers"][0]

    assert spec["strategy"]["rollingUpdate"] == {"maxSurge": 1, "maxUnavailable": 0}
    assert pod_spec["automountServiceAccountToken"] is False
    assert service_account["automountServiceAccountToken"] is False
    assert pod_spec["securityContext"]["runAsNonRoot"] is True
    assert pod_spec["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
    assert container["securityContext"]["allowPrivilegeEscalation"] is False
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
    assert container["resources"]["requests"] == {"cpu": "100m", "memory": "128Mi"}
    assert container["resources"]["limits"] == {"cpu": "500m", "memory": "256Mi"}
    for probe_name, path in (("startupProbe", "/live"), ("livenessProbe", "/live"), ("readinessProbe", "/ready")):
        assert container[probe_name]["httpGet"] == {"path": path, "port": "http"}
    assert hpa["apiVersion"] == "autoscaling/v2"
    assert hpa["spec"]["metrics"][0]["resource"]["name"] == "cpu"


def test_service_and_network_policy_are_internal_and_explicit() -> None:
    documents = render_overlay("dev")
    service = resource(documents, "Service", "platform-api")
    policy = resource(documents, "NetworkPolicy", "platform-api-restricted")

    assert service["spec"]["type"] == "ClusterIP"
    assert policy["spec"]["policyTypes"] == ["Ingress", "Egress"]
    ingress_rule = policy["spec"]["ingress"][0]
    assert ingress_rule["ports"] == [{"protocol": "TCP", "port": 8080}]
    assert ingress_rule["from"][0]["namespaceSelector"]["matchLabels"] == {
        "platform.example.io/ingress": "allowed"
    }
    egress_ports = policy["spec"]["egress"][0]["ports"]
    assert egress_ports == [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}]


def test_secret_values_and_github_actions_are_not_committed() -> None:
    yaml_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "k8s").rglob("*.yaml"))
    assert "kind: Secret" not in yaml_text
    assert "stringData:" not in yaml_text
    assert not (ROOT / ".github" / "workflows").exists()
    assert "secretKeyRef:" in yaml_text
