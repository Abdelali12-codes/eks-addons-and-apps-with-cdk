import os
import logging
import signal
import time
from threading import Thread

import kopf
import kubernetes
import structlog
from kubernetes import client, config
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from prometheus_client import Counter, start_http_server

# ---------- Configuration ----------
NAMESPACE = os.getenv("WATCH_NAMESPACE", "default")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
CM_SUFFIX = "-cm"
# -----------------------------------

# Setup structured logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
)
log = structlog.get_logger()

# Prometheus metrics
CREATES = Counter("example_operator_creates_total", "Number of created Example CRs")
UPDATES = Counter("example_operator_updates_total", "Number of updated Example CRs")
DELETES = Counter("example_operator_deletes_total", "Number of deleted Example CRs")
ERRORS = Counter("example_operator_errors_total", "Number of operator errors")

# Kubernetes clients will be created on startup by kopf lifecycle hooks
core_v1: client.CoreV1Api = None
custom_api: client.CustomObjectsApi = None

# A simple health server (runs in-thread)
def run_health_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/healthz", "/ready"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")
            elif self.path == "/metrics":
                # prometheus_client runs its own HTTP server; leave this to it
                self.send_response(404)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return  # silence stdlib logging to stdout

    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    log.info("health-server-started", port=HEALTH_PORT)
    server.serve_forever()

# Retry config: exponential backoff up to ~5 retries (adjust as needed)
retry_decorator = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type(Exception),
)

@retry_decorator
def create_or_update_configmap(name: str, namespace: str, message: str):
    cm_name = f"{name}{CM_SUFFIX}"
    data = {"message": message}
    body = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=cm_name),
        data=data
    )
    try:
        core_v1.read_namespaced_config_map(cm_name, namespace)
        core_v1.replace_namespaced_config_map(cm_name, namespace, body)
        log.info("configmap-replaced", name=cm_name, namespace=namespace)
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == 404:
            core_v1.create_namespaced_config_map(namespace, body)
            log.info("configmap-created", name=cm_name, namespace=namespace)
        else:
            log.error("configmap-error", error=e.reason, status=e.status)
            raise

@retry_decorator
def delete_configmap(name: str, namespace: str):
    cm_name = f"{name}{CM_SUFFIX}"
    try:
        core_v1.delete_namespaced_config_map(cm_name, namespace)
        log.info("configmap-deleted", name=cm_name, namespace=namespace)
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == 404:
            log.info("configmap-not-found", name=cm_name, namespace=namespace)
        else:
            log.error("configmap-delete-error", error=e.reason, status=e.status)
            raise

# Kopf startup: configure Kubernetes client and start metrics + health servers
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    global core_v1, custom_api

    # Use in-cluster config if running inside k8s, otherwise kubeconfig
    try:
        config.load_incluster_config()
        log.info("k8s-config", method="incluster")
    except Exception:
        config.load_kube_config()
        log.info("k8s-config", method="kubeconfig")

    core_v1 = client.CoreV1Api()
    custom_api = client.CustomObjectsApi()

    # Increase resync interval (optional)
    settings.posting.enabled = True
    settings.posting.level = logging.INFO

    # Kopf's default request timeout can be tuned:
    settings.networking.request_timeout = 60  # seconds

    # Start prometheus metrics server
    start_http_server(METRICS_PORT)
    log.info("prometheus-metrics-started", port=METRICS_PORT)

    # Start health server in background thread
    t = Thread(target=run_health_server, daemon=True)
    t.start()

# Leader election note:
# Kopf itself does not implement Kubernetes-style leader election out-of-the-box as a flag,
# but leader election in k8s is typically done by letting pods compete for a Lease resource.
# The simplest deployment pattern is to run replicas=2+ and allow only one active operator by
# declaring the operator logic to be guarded by a Lease-based leader election library.
# Alternatively, you can run the operator with replicas=1 and rely on Deployment upgrade strategies.
#
# For this example we include leases permission in RBAC and recommend adding a leader election
# mechanism (e.g., implement leader election with the coordination API or use libraries that
# provide this). See RBAC for Lease permission.

# Handler: on create
@kopf.on.create('my.domain', 'v1', 'examples')
def on_create(body, spec, name, namespace, **kwargs):
    try:
        message = spec.get("message", "")
        log.info("example-created", name=name, namespace=namespace, message=message)
        create_or_update_configmap(name, namespace, message)
        CREATES.inc()
        # Optionally update the status subresource
        return {"message": "configmap-created"}
    except Exception as e:
        ERRORS.inc()
        log.exception("create-handler-error", name=name, err=str(e))
        raise

# Handler: on update
@kopf.on.update('my.domain', 'v1', 'examples')
def on_update(body, spec, name, namespace, **kwargs):
    try:
        message = spec.get("message", "")
        log.info("example-updated", name=name, namespace=namespace, message=message)
        create_or_update_configmap(name, namespace, message)
        UPDATES.inc()
        return {"message": "configmap-updated"}
    except Exception as e:
        ERRORS.inc()
        log.exception("update-handler-error", name=name, err=str(e))
        raise

# Handler: on delete
@kopf.on.delete('my.domain', 'v1', 'examples')
def on_delete(body, spec, name, namespace, **kwargs):
    try:
        log.info("example-deleted", name=name, namespace=namespace)
        delete_configmap(name, namespace)
        DELETES.inc()
    except Exception as e:
        ERRORS.inc()
        log.exception("delete-handler-error", name=name, err=str(e))
        # swallow error on delete to not block finalizers (or re-raise if you want retries)

# Optional periodic reconciliation (safe guard)
@kopf.timer('my.domain', 'v1', 'examples', interval=300.0)  # every 5 minutes
def periodic_reconcile(namespace, **kwargs):
    """
    Periodically reconcile all Example CRs to ensure desired state matches actual state.
    This is useful as a defense-in-depth mechanism.
    """
    try:
        items = custom_api.list_namespaced_custom_object(
            group="my.domain",
            version="v1",
            namespace=namespace,
            plural="examples"
        ).get("items", [])
        for item in items:
            name = item["metadata"]["name"]
            message = item.get("spec", {}).get("message", "")
            try:
                create_or_update_configmap(name, namespace, message)
            except Exception as e:
                log.exception("periodic-reconcile-error", name=name, err=str(e))
                ERRORS.inc()
    except Exception as e:
        log.exception("periodic-reconcile-list-error", err=str(e))
        ERRORS.inc()
