
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## keycloak configuration
```
http://<host>:<port>/auth/realms/<realm_name>/.well-known/openid-configuration
```
## github and gitlab application redirect url
```
https://argocd.abdelalitraining.com/api/dex/callback
```
## set up gitlab server on amazon linuxx server

```


sudo dnf install -y policycoreutils-python-utils openssh-server openssh-clients perl
# Check if OpenSSH server daemon is enabled
sudo systemctl status sshd
## If OpenSSH server daemon is not enabled, enable it
sudo systemctl enable sshd
sudo systemctl start sshd


```
* for smtp server, we will use aws ses

## install package 
```

curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ee/script.rpm.sh | sudo bash
sudo EXTERNAL_URL="https://gitlab.abdelalitraining.com" dnf install gitlab-ee -y
```

## apply configuration
```
sudo gitlab-ctl reconfigure
```


### Opensearch fluent bit 

```
#Export variable ES_DOMAIN_NAME to make easier later
export ES_DOMAIN_NAME="your-app-logging" 

#Create json file for fluent-bit-policy
cat <<EoF > fluent-bit-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "es:ESHttp*"
            ],
            "Resource": "arn:aws:es:YOUR_AWS_REGION:YOUR_ACCOUNT_ID:domain/${ES_DOMAIN_NAME}",
            "Effect": "Allow"
        }
    ]
}
EoF

#Create IAM policy
aws iam create-policy   \
  --policy-name fluent-bit-policy \
  --policy-document file://fluent-bit-policy.json
```

```
eksctl create iamserviceaccount \
    --name fluent-bit \
    --namespace logging \
    --cluster YOUR_EKS_CLUSTER\
    --attach-policy-arn "arn:aws:iam::YOUR_ACCOUNT_ID:policy/fluent-bit-policy" \
    --approve \
    --override-existing-serviceaccounts

#Check service account is created
kubectl describe sa fluent-bit -n logging
```

```
- Before that, please export these variables :

# name of our Amazon OpenSearch cluster
export ES_DOMAIN_NAME="your-app-logging"

# Opensearch latest version when this article is published. You can change with your needed.
export ES_VERSION="OpenSearch_2.7"

# OpenSearch Dashboards admin user, you can change also this to what you want.
export ES_DOMAIN_USER="something-you-can-remember"

# OpenSearch Dashboards admin password
export ES_DOMAIN_PASSWORD="$(openssl rand -base64 15)_Ek1$"

# Remember this all variables
echo "OpenSearch Domain Name: ${ES_DOMAIN_NAME}
OpenSearch Dashboards user: ${ES_DOMAIN_USER}
OpenSearch Dashboards password: ${ES_DOMAIN_PASSWORD}"
```

```
{
    "DomainName": "YOUR_ES_DOMAIN_NAME",
    "EngineVersion": "OpenSearch_2.7",
    "ClusterConfig": {
        "InstanceType": "m4.large.search",
        "InstanceCount": 1,
            "DedicatedMasterEnabled": false,
            "ZoneAwarenessEnabled": false,
            "WarmEnabled": false
        },
    "EBSOptions": {
        "EBSEnabled": true,
        "VolumeType": "gp2",
        "VolumeSize": 20
    },
    "AccessPolicies":  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":\"es:ESHttp*\",\"Resource\":\"arn:aws:es:YOUR_AWS_REGION:YOUR_ACCOUNT_ID:domain/YOUR_ES_DOMAIN_NAME/*\"}]}",
    "SnapshotOptions": {},
    "CognitoOptions": {
        "Enabled": false
    },
    "EncryptionAtRestOptions": {
        "Enabled": true
    },
    "NodeToNodeEncryptionOptions": {
        "Enabled": true
    },
    "DomainEndpointOptions": {
        "EnforceHTTPS": true,
        "TLSSecurityPolicy": "Policy-Min-TLS-1-0-2019-07"
    },
    "AdvancedSecurityOptions": {
        "Enabled": true,
        "InternalUserDatabaseEnabled": true,
        "MasterUserOptions": {
            "MasterUserName": "YOUR_ES_DOMAIN_USER",
            "MasterUserPassword": "YOUR_ES_DOMAIN_PASSWORD"
        }
    }
}
```

```
# Get Role ARN
eksctl get iamserviceaccount --cluster YOUR_CLUSTER_NAME --namespace logging -o json

#After that, copy the roleARN value for example
arn:aws:iam::012345678910:role/your-cluster-name-addon-iamservice-Role1-A1B2C3D4E5F6

#Export this arn to FLUENTBIT_ROLE varaible
export FLUENTBIT_ROLE=arn:aws:iam::012345678910:role/your-cluster-name-addon-iamservice-Role1-A1B2C3D4E5F6

# Get the Amazon OpenSearch Endpoint
export ES_ENDPOINT=$(aws opensearch describe-domain --domain-name ${ES_DOMAIN_NAME} --output text --query "DomainStatus.Endpoint")

# Update the Opensearch internal database
curl -sS -u "${ES_DOMAIN_USER}:${ES_DOMAIN_PASSWORD}" \
    -X PATCH \
    https://${ES_ENDPOINT}/_opendistro/_security/api/rolesmapping/all_access?pretty \
    -H 'Content-Type: application/json' \
    -d'
[
  {
    "op": "add", "path": "/backend_roles", "value": ["'${FLUENTBIT_ROLE}'"]
  }
]
'
```


```
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluent-bit-read
rules:
- apiGroups: [""]
  resources:
  - namespaces
  - pods
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: fluent-bit-read
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: fluent-bit-read
subjects:
- kind: ServiceAccount
  name: fluent-bit
  namespace: logging
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
  labels:
    k8s-app: fluent-bit
data:
  # Configuration files: server, input, filters and output
  # ======================================================
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    @INCLUDE input-kubernetes.conf
    @INCLUDE filter-kubernetes.conf
    @INCLUDE output-elasticsearch.conf

  input-kubernetes.conf: |
    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            docker
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10

  filter-kubernetes.conf: |
    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Kube_Tag_Prefix     kube.var.log.containers.
        Merge_Log           On
        Merge_Log_Key       log_processed
        K8S-Logging.Parser  On
        K8S-Logging.Exclude Off

  output-elasticsearch.conf: |
    [OUTPUT]
        Name            es
        Match           *
        Host            YOUR_ES_ENDPOINT
        Port            443
        TLS             On
        AWS_Auth        On
        AWS_Region      YOUR_AWS_REGION
        Retry_Limit     6
        Index           fluent-bit
        Suppress_Type_Name On

  parsers.conf: |
    [PARSER]
        Name   apache
        Format regex
        Regex  ^(?<host>[^ ]*) [^ ]* (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   apache2
        Format regex
        Regex  ^(?<host>[^ ]*) [^ ]* (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^ ]*) +\S*)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   apache_error
        Format regex
        Regex  ^\[[^ ]* (?<time>[^\]]*)\] \[(?<level>[^\]]*)\](?: \[pid (?<pid>[^\]]*)\])?( \[client (?<client>[^\]]*)\])? (?<message>.*)$

    [PARSER]
        Name   nginx
        Format regex
        Regex ^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   json
        Format json
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name        docker
        Format      json
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On

    [PARSER]
        Name        syslog
        Format      regex
        Regex       ^\<(?<pri>[0-9]+)\>(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
        Time_Key    time
        Time_Format %b %d %H:%M:%S
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
  labels:
    k8s-app: fluent-bit-logging
    version: v1
    kubernetes.io/cluster-service: "true"

spec:
  selector:
    matchLabels:
      k8s-app: fluent-bit-logging
  template:
    metadata:
      labels:
        k8s-app: fluent-bit-logging
        version: v1
        kubernetes.io/cluster-service: "true"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "2020"
        prometheus.io/path: /api/v1/metrics/prometheus
    spec:
      containers:
      - name: fluent-bit
        image: amazon/aws-for-fluent-bit:latest
        imagePullPolicy: Always
        ports:
          - containerPort: 2020
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc/
      terminationGracePeriodSeconds: 10
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
      serviceAccountName: fluent-bit
```

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/eksctl-your-eks-cluster-addon-iamservice-Role-ABCDEFGHIJK"
      },
      "Action": "es:ESHttp*",
      "Resource": "arn:aws:es:YOUR_AWS_REGION:YOUR_ACCOUNT_ID:domain/YOUR_ES_DOMAIN_NAME/*"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "es:ESHttp*",
      "Resource": "arn:aws:es:YOUR_AWS_REGION:YOUR_ACCOUNT_ID:domain/YOUR_ES_DOMAIN_NAME/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": [
            "AA.BB.CC.DD/32",
            "EE.FF.GG.HH/32"
          ]
        }
      }
    }
  ]
}
# AWS EKS Addons Compatibility 
```
aws eks describe-addon-versions --addon-name adot --kubernetes-version eks-version
```

# Run Grafana Enterprise
```
docker run  -d -p 3000:3000 --name=grafanaen -v  "C:/Users/Abdelali Jadelmoula/data:/usr/share/grafana/.aws/:ro"  -e AWS_SDK_LOAD_CONFIG=true -e GF_AUTH_SIGV4_AUTH_ENABLED=true grafana/grafana-enterprise
```

# Metrics (Metrics Server)
```
kubectl get --raw "/apis/metrics.k8s.io/v1beta2" | jq .
```
# Custom metrics
```
# you can pipe to `jq .` to pretty-print the output, if it's installed
# (otherwise, it's not necessary)
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta2" | jq .
# fetching certain custom metrics of namespaced resources
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta2/namespaces/default/services/kubernetes/test-metric" | jq .
```

# external metrics

```
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1" | jq .
# fetching certain custom metrics of namespaced resources
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/default/my-external-metric" | jq .
```