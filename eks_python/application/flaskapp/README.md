# DNAT with iptables – Kubernetes kube-proxy Simulation Lab

This lab demonstrates how **iptables DNAT rules** are used to forward traffic from a "NodePort" to a backend application — similar to how Kubernetes `kube-proxy` works in `iptables` mode.

---

## 🧩 Lab Goal
- Simulate a Kubernetes **NodePort Service** (`:30080`)
- Forward traffic from `localhost:30080` → backend app (`localhost:8080`)

---

## 🧪 Steps

### 1. Start a Backend Server
Run a simple HTTP server on port **8080**:
```bash
python3 -m http.server 8080
```

Verify:

`   curl http://127.0.0.1:8080   `

### 2\. Add DNAT Rules

Create DNAT rules so that traffic hitting :30080 gets forwarded to :8080.

`   sudo iptables -t nat -A PREROUTING -p tcp --dport 30080 -j DNAT --to-destination 127.0.0.1:8080 `


` sudo iptables -t nat -A OUTPUT -p tcp --dport 30080 -j DNAT --to-destination 127.0.0.1:8080   `

*   **PREROUTING**: handles traffic arriving from outside the host.
    
*   **OUTPUT**: ensures local traffic to localhost:30080 is also redirected.
    

### 3\. (Optional) Allow Forwarding

If the backend is on another host/container:

`   sudo iptables -A FORWARD -p tcp -d 127.0.0.1 --dport 8080 -j ACCEPT   `

### 4\. Test NodePort Access

`   curl http://127.0.0.1:30080   `

✅ You should see the same response as hitting :8080, but traffic was DNAT’ed by iptables.

### 5\. Inspect Rules

`   sudo iptables -t nat -L -n -v   `

### 6\. Cleanup

When finished:

`   sudo iptables -t nat -F   `

🔎 How This Relates to Kubernetes
---------------------------------

*   In Kubernetes, a **Service** of type NodePort automatically gets a port (e.g., 30080).
    
*   kube-proxy installs DNAT rules so that NodeIP:30080 forwards to one of the backend **pod IPs**.
    
*   If multiple pods back the Service, iptables rules round-robin across them.


## Kube-Proxy and Service

🔹 1. Service and Endpoint Objects
----------------------------------

When you create a Service in Kubernetes:


```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
  type: NodePort
Kubernetes creates:
```

*   **Service object** → defines a _virtual IP_ (ClusterIP) and/or NodePort.
    
*   **EndpointSlice (or Endpoints)** → lists the _real pod IPs_ backing this Service.
    

Example EndpointSlice:

# Kubernetes EndpointSlice Example

This example shows how Kubernetes tracks Pod IPs for a Service using **EndpointSlice**.

## EndpointSlice Manifest

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: my-service-xxxx
addressType: IPv4
ports:
  - port: 8080
endpoints:
  - addresses: ["10.42.1.23"]   # Pod IP 1
  - addresses: ["10.42.2.45"]   # Pod IP 2
```

So:

*   Service = stable _frontend_
    
*   Endpoints = list of _backends_ (pod IPs)
    

🔹 2. Role of kube-proxy
------------------------

kube-proxy runs as a DaemonSet (or system component) on **every node**.It **watches the API server** for Service and Endpoint changes.

Based on that info, kube-proxy programs the **Linux networking rules** so traffic is redirected to pods.

🔹 3. How kube-proxy sets up forwarding
---------------------------------------

### Case A: ClusterIP Service

*   ClusterIP (like 10.96.0.1:80) is **virtual**; it doesn’t exist on any interface.
    
*   kube-proxy creates an **iptables chain** (or IPVS virtual server) that DNATs traffic from the ClusterIP → one of the pod IPs in the Endpoints.
    

Example rule (simplified):

`   -A KUBE-SERVICES -d 10.96.0.1/32 -p tcp --dport 80 -j KUBE-SVC-XYZ  -A KUBE-SVC-XYZ -m statistic --mode random --probability 0.5 -j KUBE-SEP-ABC  -A KUBE-SVC-XYZ -j KUBE-SEP-DEF  -A KUBE-SEP-ABC -j DNAT --to-destination 10.42.1.23:8080  -A KUBE-SEP-DEF -j DNAT --to-destination 10.42.2.45:8080   `

This means:

*   Any packet to 10.96.0.1:80 → redirected to one of the pods.
    
*   statistic --probability gives a form of load balancing (random/round robin).
    

### Case B: NodePort Service

*   kube-proxy adds rules for the NodePort (e.g., :30080).
    
*   Packets arriving at NodeIP:30080 are DNAT’ed to the **same backend chain** as the ClusterIP.
    

So:

`   Client → NodeIP:30080 → kube-proxy iptables → PodIP:8080   `

### Case C: LoadBalancer Service (AWS NLB/ELB)

*   AWS creates an external LB that forwards to the NodePort.
    
*   kube-proxy handles traffic the same as NodePort.
    
*   Or, if using nlb-ip mode, the NLB sends directly to Pod IPs (kube-proxy is bypassed).
    

🔹 4. kube-proxy Modes
----------------------

*   **iptables mode** (default):
    
    *   Programs DNAT rules with iptables.
        
    *   Load balancing is done via random selection (statistic match).
        
*   **IPVS mode**:
    
    *   Uses Linux IPVS (kernel-level LB).
        
    *   Scales better with many services/pods.
        

🔹 5. Key Idea
--------------

*   Service gives a **stable virtual identity** (ClusterIP, NodePort).
    
*   Endpoints map that to **real pods**.
    
*   kube-proxy takes those and **programs iptables/IPVS** so the kernel forwards packets automatically.
    
*   kube-proxy itself does not sit in the data path; it’s only the “rule manager.”
    

📌 **Analogy:**Think of Service as a company’s **public phone number**, Endpoints as the **employee desk phones**, and kube-proxy as the **PBX switchboard configuration** that routes calls behind the scenes.