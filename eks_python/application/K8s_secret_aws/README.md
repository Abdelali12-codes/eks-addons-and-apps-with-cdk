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