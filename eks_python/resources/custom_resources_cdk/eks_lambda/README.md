**1️⃣ Context: How the token is issued**
----------------------------------------

1.  You run:
    

`   aws eks get-token --cluster-name my-cluster   `

1.  The AWS CLI calls **STS** to issue a temporary token using your IAM credentials (or an IAM role you assume).
    
    *   Internally, it may call:
        

`   sts:GetCallerIdentity  sts:AssumeRoleWithWebIdentity   `

1.  STS returns a **JWT** that contains:
    
    *   The IAM identity (role or user ARN) in the sub field
        
    *   Expiration (exp) and issued at (iat)
        
    *   Audience (aud)
        
    *   Other claims
        
2.  The token is prepended with k8s-aws-v1. to indicate to EKS that this is an AWS IAM token.
    

**2️⃣ Token reaches Kubernetes API server**
-------------------------------------------

When you run:

`   kubectl get pods   `

*   kubectl sends:
    

`   Authorization: Bearer k8s-aws-v1.   `

*   EKS API server forwards the token to the **AWS IAM Authenticator webhook** (or built-in EKS authenticator).
    

**3️⃣ How the Authenticator validates the token**
-------------------------------------------------

1.  **Checks the prefix**
    
    *   The token must start with k8s-aws-v1..
        
    *   If missing, it rejects the token.
        
2.  **Strips the prefix** and decodes the JWT payload.
    
3.  **Verifies the signature** of the JWT using AWS STS public keys.
    
    *   STS signs the token with its private key.
        
    *   Authenticator fetches the **JWKS (JSON Web Key Set)** from STS to verify the signature.
        
4.  **Checks token validity**
    
    *   Expiration (exp) is in the future.
        
    *   Issued-at (iat) is in the past.
        
    *   Audience (aud) matches expected value (sts.amazonaws.com or kubernetes).
        
5.  **Extracts the caller identity** from the sub field:
    

`   sub: arn:aws:iam::123456789012:role/EKS-Admin   `

*   This tells the authenticator **which IAM user or role made the request**.
    

**4️⃣ Maps IAM identity to Kubernetes RBAC**
--------------------------------------------

*   The authenticator uses the aws-auth ConfigMap in the kube-system namespace:
    

`   mapRoles: |    - rolearn: arn:aws:iam::123456789012:role/EKS-Admin      username: admin      groups:        - system:masters  mapUsers: |    - userarn: arn:aws:iam::123456789012:user/alice      username: alice      groups:        - developers   `

*   The IAM role/user in sub is **mapped to a Kubernetes username and groups**.
    
*   This determines **what permissions the caller has** in Kubernetes.
    

**5️⃣ Summary of steps**
------------------------


| Step | Action |
|------|--------|
| 1    | `kubectl` runs and requests token via `aws eks get-token` |
| 2    | AWS STS issues JWT containing IAM ARN |
| 3    | `kubectl` sends `Authorization: Bearer k8s-aws-v1.<jwt>` to API server |
| 4    | API server passes token to AWS IAM Authenticator |
| 5    | Authenticator strips prefix, verifies JWT signature with STS public keys |
| 6    | Authenticator extracts IAM ARN from token (`sub`) |
| 7    | Maps IAM ARN to Kubernetes username/groups via `aws-auth` ConfigMap |
| 8    | Access granted/denied based on Kubernetes RBAC |


✅ **Key points**

*   The authenticator **does not trust the token blindly**; it verifies it cryptographically using STS keys.
    
*   It uses the **IAM ARN in the token** to determine the caller.
    
*   RBAC in Kubernetes (mapRoles / mapUsers) determines permissions.