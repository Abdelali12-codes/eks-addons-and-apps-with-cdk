# Kubernetes ServiceAccount & AWS IRSA Tokens

When running workloads on **Kubernetes (EKS)**, a pod that uses a `ServiceAccount` can have **two different tokens**.  
This allows the pod to talk securely to **both Kubernetes** and **AWS**.

---

## 🔹 1. Two Tokens in Play

### Kubernetes ServiceAccount Token
- **Mounted at:**  
  `/var/run/secrets/kubernetes.io/serviceaccount/token`
- **Purpose:**  
  - JWT used to authenticate to the Kubernetes API server.  
  - Consumed by the `kubernetes-python-client` when calling `load_incluster_config()`.

---

### AWS Web Identity Token (IRSA)
- **Mounted at (by EKS if annotated with IAM Role ARN):**  
  `/var/run/secrets/eks.amazonaws.com/serviceaccount/token`
- **Purpose:**  
  - JWT that `boto3` (via the AWS SDK credential provider chain) uses to call `sts:AssumeRoleWithWebIdentity`.  
  - Allows the pod to **assume the IAM Role linked to its ServiceAccount**.

---

## 🔹 2. How boto3 Finds the Token

You don’t need to explicitly load the token.  
EKS injects environment variables when **IRSA** is enabled:

```bash
AWS_ROLE_ARN=arn:aws:iam::<ACCOUNT_ID>:role/MyAppRole
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

Then boto3 does the following automatically:

1.  Reads the token from $AWS\_WEB\_IDENTITY\_TOKEN\_FILE.
    
2.  Calls sts:AssumeRoleWithWebIdentity for $AWS\_ROLE\_ARN.
    
3.  Gets temporary AWS credentials (AccessKeyId, SecretAccessKey, SessionToken).
    
4.  Uses those credentials for AWS API calls ✅
    

🔹 3. Verifying Inside a Pod
----------------------------

Check the environment and mounted files:

`   env | grep AWS  # AWS_ROLE_ARN=arn:aws:iam:::role/MyAppRole  # AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token  ls /var/run/secrets/eks.amazonaws.com/serviceaccount/  # ca.crt  namespace  token   `

> ⚠️ You _can_ cat the token (JWT), but it’s meant for AWS STS and should not be exposed.

🔹 4. Summary
-------------

*   **Kubernetes API token**
    
    *   Path: /var/run/secrets/kubernetes.io/serviceaccount/token
        
    *   Used by Kubernetes clients.
        
*   **AWS Web Identity token (IRSA)**
    
    *   Path: /var/run/secrets/eks.amazonaws.com/serviceaccount/token
        
    *   Used by boto3 to assume IAM roles.
        

✅ This setup allows a pod to securely communicate with **both Kubernetes and AWS**, each with its own identity.


### **config.load\_incluster\_config() in Kubernetes Python client**

This function is part of the **kubernetes Python client** (kubernetes.client.config). It’s used when your Python code runs **inside a pod** and wants to talk to the Kubernetes API server.

When you call:

`   from kubernetes import config  config.load_incluster_config()   `

it **automatically consumes certain files and environment variables that are available inside the pod**.

### **What it reads by default**

1.  /var/run/secrets/kubernetes.io/serviceaccount/token
    
    *   This is a JWT token associated with the pod's service account.
        
    *   Used for authenticating the pod to the Kubernetes API server.
        
2.  /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    
    *   Used to validate the Kubernetes API server’s SSL certificate.
        
3.  /var/run/secrets/kubernetes.io/serviceaccount/namespace
    
    *   The namespace in which the pod is running.
        
4.  KUBERNETES\_SERVICE\_HOST KUBERNETES\_SERVICE\_PORT
    
    *   These are automatically injected into the pod by Kubernetes.
        
    *   load\_incluster\_config constructs the API server endpoint from these.
        

### **What’s available inside the pod environment**

If you look at a pod:

`   env | grep KUBERNETES  # Example:  # KUBERNETES_SERVICE_HOST=10.0.0.1  # KUBERNETES_SERVICE_PORT=443   `

And the service account files:

`   ls /var/run/secrets/kubernetes.io/serviceaccount/  # ca.crt  namespace  token   `

These three pieces plus the service host/port are **exactly what load\_incluster\_config() consumes** to set up the Kubernetes client configuration.

### ✅ **Summary**

### Kubernetes In-Cluster Config Summary

| Component                 | Path / Environment Variable                                      | Purpose                                      |
|----------------------------|-----------------------------------------------------------------|----------------------------------------------|
| Service Account Token      | `/var/run/secrets/kubernetes.io/serviceaccount/token`           | Authenticate pod to Kubernetes API          |
| CA Certificate             | `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`          | Validate API server SSL                      |
| Namespace                  | `/var/run/secrets/kubernetes.io/serviceaccount/namespace`       | Identify the pod’s namespace                |
| Kubernetes API URL         | `KUBERNETES_SERVICE_HOST` + `KUBERNETES_SERVICE_PORT`           | Endpoint to connect to Kubernetes API server|


So, when you call config.load\_incluster\_config(), **all of this is automatically picked up**—no need to pass anything manually.