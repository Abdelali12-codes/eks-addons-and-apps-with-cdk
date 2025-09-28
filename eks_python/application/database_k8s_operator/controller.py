import kopf
import kubernetes
import secrets
import base64

# Load cluster config (when running inside Kubernetes)
kubernetes.config.load_incluster_config()

def generate_password(length=16):
    return base64.b64encode(secrets.token_bytes(length)).decode("utf-8")

@kopf.on.create('mycompany.com', 'v1alpha1', 'databases')
def create_database(spec, meta, name, namespace, **kwargs):
    engine = spec.get('engine')
    version = spec.get('version')
    storage = spec.get('storage')

    annotations = meta.get("annotations", {})
    backup_enabled = annotations.get("backup/enabled", "false")
    backup_schedule = annotations.get("backup/schedule", None)

    print(f"Provisioning DB {name}: engine={engine}, version={version}, storage={storage}")

    core_api = kubernetes.client.CoreV1Api()
    apps_api = kubernetes.client.AppsV1Api()
    batch_api = kubernetes.client.BatchV1Api()

    # ----------------------------------------------------------------
    # 1. Secret for DB credentials
    # ----------------------------------------------------------------
    username = "admin"
    password = generate_password(12)
    secret = kubernetes.client.V1Secret(
        metadata=kubernetes.client.V1ObjectMeta(name=f"{name}-secret", namespace=namespace),
        string_data={"username": username, "password": password}
    )
    core_api.create_namespaced_secret(namespace=namespace, body=secret)

    # ----------------------------------------------------------------
    # 2. StatefulSet for Postgres
    # ----------------------------------------------------------------
    statefulset = {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "serviceName": name,
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [{
                        "name": engine,
                        "image": f"{engine}:{version}",
                        "ports": [{"containerPort": 5432}],
                        "env": [
                            {"name": "POSTGRES_USER", "valueFrom": {"secretKeyRef": {"name": f"{name}-secret", "key": "username"}}},
                            {"name": "POSTGRES_PASSWORD", "valueFrom": {"secretKeyRef": {"name": f"{name}-secret", "key": "password"}}}
                        ],
                        "volumeMounts": [{
                            "mountPath": "/var/lib/postgresql/data",
                            "name": "db-storage"
                        }]
                    }]
                }
            },
            "volumeClaimTemplates": [{
                "metadata": {"name": "db-storage"},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": storage}}
                }
            }]
        }
    }
    apps_api.create_namespaced_stateful_set(namespace=namespace, body=statefulset)

    # ----------------------------------------------------------------
    # 3. Service for Postgres
    # ----------------------------------------------------------------
    service = kubernetes.client.V1Service(
        metadata=kubernetes.client.V1ObjectMeta(name=name, namespace=namespace),
        spec=kubernetes.client.V1ServiceSpec(
            selector={"app": name},
            ports=[kubernetes.client.V1ServicePort(port=5432, target_port=5432)]
        )
    )
    core_api.create_namespaced_service(namespace=namespace, body=service)

    # ----------------------------------------------------------------
    # 4. Backup CronJob (if enabled)
    # ----------------------------------------------------------------
    if backup_enabled.lower() == "true" and backup_schedule:
        cronjob = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {"name": f"{name}-backup", "namespace": namespace},
            "spec": {
                "schedule": backup_schedule,
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "restartPolicy": "OnFailure",
                                "containers": [{
                                    "name": "backup",
                                    "image": "postgres:15",  # uses pg_dump
                                    "command": ["/bin/sh", "-c"],
                                    "args": [
                                        "pg_dump -h {0} -U $POSTGRES_USER > /backup/{0}-$(date +%F).sql".format(name)
                                    ],
                                    "env": [
                                        {"name": "POSTGRES_USER", "valueFrom": {"secretKeyRef": {"name": f"{name}-secret", "key": "username"}}},
                                        {"name": "POSTGRES_PASSWORD", "valueFrom": {"secretKeyRef": {"name": f"{name}-secret", "key": "password"}}}
                                    ],
                                    "volumeMounts": [{
                                        "mountPath": "/backup",
                                        "name": "backup-storage"
                                    }]
                                }],
                                "volumes": [{
                                    "name": "backup-storage",
                                    "emptyDir": {}  # could be PVC or S3 sidecar in real-world
                                }]
                            }
                        }
                    }
                }
            }
        }
        batch_api.create_namespaced_cron_job(namespace=namespace, body=cronjob)
        print(f"Backup CronJob created for {name} with schedule {backup_schedule}")

    return {"message": f"Database {name} provisioned with {engine}:{version} and {storage} storage."}
