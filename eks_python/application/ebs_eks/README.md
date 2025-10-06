Let’s go step by step on how an **EBS volume** actually gets mounted to a pod in Kubernetes.

🔹 Flow: Pod → PVC → PV → EBS
-----------------------------

1.  volumes: - name: data persistentVolumeClaim: claimName: myapp-pvc
    
2.  apiVersion: v1kind: PersistentVolumeClaimmetadata: name: myapp-pvcspec: accessModes: - ReadWriteOnce resources: requests: storage: 10Gi storageClassName: gp2
    
    *   The PVC asks for storage (storageClassName, size, accessModes).
        
    *   Kubernetes finds (or dynamically provisions) a matching PersistentVolume (PV).
        
3.  apiVersion: storage.k8s.io/v1kind: StorageClassmetadata: name: gp2provisioner: ebs.csi.aws.comvolumeBindingMode: WaitForFirstConsumer
    
    *   The StorageClass tells Kubernetes which **provisioner** to use (for EBS, that’s the **EBS CSI driver**).
        
    
    *   The **EBS CSI controller** talks to AWS APIs → creates an **EBS volume** in your AWS account.
        
4.  **Attach EBS to node**
    
    *   The **EBS CSI node plugin** runs as a DaemonSet on every node.
        
    *   When a Pod using the PVC is scheduled to Node X, the plugin:
        
        1.  Calls AWS API → AttachVolume (attaches EBS to Node X).
            
        2.  Waits for Linux kernel to see the device (e.g. /dev/nvme1n1).
            
        3.  Formats it if it’s new (ext4/xfs).
            
        4.  Mounts it on the node’s filesystem (e.g. /var/lib/kubelet/pods//volumes/kubernetes.io~csi/pv-name/mount).
            
5.  **Bind mount into Pod**
    
    *   Finally, kubelet bind-mounts that directory into the container’s mount path (/data in your Pod spec).
        

🔹 Visual Flow
--------------

`   Pod (mountPath /data)     |     v  kubelet bind mount     |     v  Node filesystem: /var/lib/kubelet/pods//volumes/...     |     v  EBS CSI node plugin → attaches EBS (/dev/nvmeXnY) → mounts to host     |     v  AWS EBS volume (gp2/gp3/etc)   `

🔹 Key Points
-------------

*   **One pod at a time**: EBS is ReadWriteOnce → only one node can mount it at a time.
    
*   **CSI driver does the heavy lifting**: attaches, formats, and mounts.
    
*   **Persistence**: When pod restarts on the same or another node, Kubernetes reattaches the same EBS volume → data persists.

# Kubelet Mount

This is the _last mile_ step — after the CSI driver attaches and mounts the EBS volume on the node, **kubelet does a bind mount into the container’s filesystem**.

Let’s walk through it.

🔹 What is a Bind Mount?
------------------------

In Linux, a **bind mount** makes the same directory visible in two places.Example:

```
mkdir /mnt/data  
mount /dev/nvme1n1 /mnt/data  
mkdir /app/data  
mount --bind /mnt/data /app/data   
```

*   /mnt/data and /app/data now show the same files.
    
*   This is exactly what kubelet does when giving a Pod access to a volume.
    

🔹 How kubelet Does It
----------------------

1.  /var/lib/kubelet/plugins/kubernetes.io/csi/pv/pv-1234/globalmount(This is the “real” filesystem from the EBS device, e.g. ext4).
    
2.  /var/lib/kubelet/pods//volumes/kubernetes.io~csi/pv-1234/
    
3.  mount --bind \\ /var/lib/kubelet/plugins/kubernetes.io/csi/pv/pv-1234/globalmount \\ /var/lib/kubelet/pods//volumes/kubernetes.io~csi/pv-1234/
    
4.  So inside the container you just see:/data → backed by EBS volume
    
    *   kubelet tells it: _“Mount /var/lib/kubelet/pods/.../volumes/... into /data inside the container.”_
        
    *   This is done via container runtime APIs (e.g., containerd Mount spec).
        

🔹 Visual Example
-----------------

`   AWS EBS (/dev/nvme1n1)     │     └── mounted by CSI → /var/lib/kubelet/plugins/kubernetes.io/csi/pv-1234/globalmount            │            └── kubelet bind-mount → /var/lib/kubelet/pods//volumes/.../pv-1234                    │                    └── container runtime mounts into container at /data   `

🔹 Why Bind Mount Instead of Direct Mount?
------------------------------------------

*   Performance: avoids remounting device per container.
    
*   Sharing: multiple containers in the same pod can bind the same volume.
    
*   Cleanup: when pod is deleted, kubelet just unmounts the bind mount — the global mount stays until volume is detached.


When a pod with a PVC is scheduled, the **EBS CSI driver** needs to attach the EBS volume to the **same EC2 instance** where the pod is running.

🔹 Flow of “who knows what”
---------------------------

1.  **Kubernetes Scheduler**
    
    *   Looks at the PVC’s access mode (ReadWriteOnce) and the StorageClass binding mode (WaitForFirstConsumer).
        
    *   Schedules the pod onto a specific node (i.e., an EC2 instance).
        
2.  **Kubelet on that node**
    
    *   Sees the pod spec includes a volume.
        
    *   Asks the **EBS CSI Node Plugin** running on that node to mount it.
        
3.  👉 This is how it “knows”: kubelet includes the **node name** in its request to the CSI driver.
    
    *   Handles **AttachVolume/DetachVolume** requests.
        
    *   Talks to AWS APIs (ec2:AttachVolume, ec2:DetachVolume).
        
    *   Decides _which node_ (EC2 instance) to attach the volume to, based on the pod’s assigned node.
        
4.  **EBS CSI Node Plugin** (DaemonSet, runs on every node)
    
    *   Runs only on the **node where the pod is scheduled**.
        
    *   Uses **EC2 instance metadata service (IMDS)** to discover its own AWS identity:
        
        *   Instance ID (i-0abcd12345…)
            
        *   Availability Zone (us-east-1a)
            
    *   When it gets a request, it knows “I am node i-0abcd12345 in us-east-1a.”
        
5.  **Controller plugin + Node plugin coordination**
    
    *   aws ec2 attach-volume --volume-id vol-0abc123 --instance-id i-0abcd12345 --device /dev/nvme1n1
        
    *   AWS attaches the volume to that EC2.
        
    *   Node plugin then sees /dev/nvme1n1, formats it if needed, and mounts it.
        

🔹 Key Mechanism
----------------

*   **Scheduler picks the node.**
    
*   **Kubelet tells CSI which node it’s on.**
    
*   **Node plugin uses IMDS (instance metadata) to confirm “I’m this EC2.”**
    
*   **Controller plugin does the AWS API call to attach volume to that EC2.**
    

🔹 Example: Instance Metadata
-----------------------------

On an EC2 instance, the CSI node plugin queries:

```
curl -s http://169.254.169.254/latest/meta-data/instance-id  # i-0abcd12345  

curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone  # us-east-1a 
```

This is how it _knows which EC2 it is running on_.

✅ So the short answer:The **EBS CSI node plugin** knows which EC2 it runs on via the **EC2 Instance Metadata Service (IMDS)**. The **EBS CSI controller plugin** decides which instance to attach the volume to, based on where Kubernetes scheduled the pod.


🔹 Steps of Pod Deployment → Running
====================================

### 1\. **kubectl apply**

*   You submit a Pod manifest (or Deployment, StatefulSet, etc.) with kubectl.
    
*   The manifest goes to the **API Server**.
    
*   The API Server stores the Pod spec in **etcd** (the cluster database).
    

### 2\. **Scheduler decides node**

*   The Pod is created in Pending phase.
    
*   The **kube-scheduler**:
    
    1.  Looks at resource requests (CPU, memory).
        
    2.  Filters candidate nodes (e.g., labels, affinity, taints/tolerations).
        
    3.  Chooses one node.
        
*   It updates the Pod spec with .spec.nodeName.
    

### 3\. **Kubelet sees assigned Pod**

*   On that node, the **kubelet** continuously watches the API Server.
    
*   It sees: “A new Pod assigned to me.”
    
*   Now it’s kubelet’s job to make it real.
    

### 4\. **Volume setup (if any)**

*   If the Pod uses PVCs:
    
    *   **CSI Controller plugin**: attaches cloud volumes (e.g., AWS EBS) to the node.
        
    *   **CSI Node plugin**: mounts the device (e.g., /dev/nvme1n1) into host filesystem.
        
*   /var/lib/kubelet/pods//volumes/...
    

### 5\. **Networking setup**

*   kubelet asks **CNI plugin** (like AWS VPC CNI, Calico, Cilium, etc.) to:
    
    *   Create a network namespace for the Pod.
        
    *   Allocate IP address.
        
    *   Attach veth pair (Pod ↔ host network).
        
    *   Program iptables/ipvs (via kube-proxy) for Services.
        

### 6\. **Init containers (if defined)**

*   If the Pod spec has initContainers, kubelet runs them **sequentially**.
    
*   They must all succeed before app containers start.
    

### 7\. **App containers start**

*   kubelet calls the **container runtime** (containerd, CRI-O, etc.) via the CRI (Container Runtime Interface).
    
*   Container runtime:
    
    1.  Pulls image (if not cached).
        
    2.  Creates container filesystem.
        
    3.  Sets up namespaces (PID, net, IPC, mount, UTS).
        
    4.  Applies **securityContext** (UID/GID, capabilities, seccomp).
        
    5.  Starts the container process (usually PID 1 inside namespace).
        

### 8\. **Probes & readiness**

*   kubelet runs **livenessProbe** and **readinessProbe** if defined.
    
*   If readiness succeeds, kubelet tells API Server: _“Pod is Ready”_.
    

### 9\. **Pod Running**

*   At this point:
    
    *   Containers are running inside their isolated namespaces.
        
    *   Volumes are mounted.
        
    *   Networking is set up.
        
*   Pod phase = **Running**.
    

🔹 Summary Flow
---------------

`   kubectl apply     ↓  API Server → etcd     ↓  Scheduler assigns node     ↓  Kubelet on node:     • Setup volumes (CSI)     • Setup networking (CNI)     • Run initContainers     • Start containers (containerd)     • Run probes     ↓  Pod phase = Running ✅   `


🔹 What is CNI?
===============

CNI = **Container Network Interface**.It’s a Linux networking standard that Kubernetes (and other runtimes) use to plug containers into a network.

*   Defined by the [CNI spec](https://github.com/containernetworking/cni).
    
*   Implemented by plugins (AWS VPC CNI, Calico, Cilium, Flannel, Weave, etc).
    
*   Kubelet doesn’t do networking itself → it just calls the **CNI plugin** when a Pod is created.
    

🔹 How it Works Step by Step
============================

### 1\. Pod Creation

*   Scheduler assigns the Pod to a node.
    
*   Kubelet asks container runtime (containerd/CRI-O) to create sandbox (network namespace).
    
*   Container runtime calls kubelet: _“I need networking for this Pod.”_
    

### 2\. Kubelet invokes CNI

*   Kubelet runs the **CNI plugin binary** located in /opt/cni/bin/.
    
*   { "cniVersion": "0.4.0", "name": "k8s-pod-network", "type": "cilium", // or aws-vpc, calico, flannel, etc "containerId": "", "netns": "/proc/12345/ns/net", "ifName": "eth0", "args": { "K8S\_POD\_NAMESPACE": "default", "K8S\_POD\_NAME": "mypod", "K8S\_POD\_INFRA\_CONTAINER\_ID": "abc123" }}
    

### 3\. CNI plugin sets up networking

Depending on the plugin:

*   **AWS VPC CNI**
    
    *   Allocates a secondary ENI IP from the VPC subnet.
        
    *   Attaches it to the node’s ENI.
        
    *   Moves that IP into the Pod’s netns.
        
*   **Calico / Cilium / Flannel**
    
    *   Creates a **veth pair** (virtual ethernet cable).
        
        *   One end goes into Pod’s netns as eth0.
            
        *   Other end stays in host netns.
            
    *   Configures Pod IP (from cluster CIDR).
        
    *   Programs routes/iptables for cross-node traffic.
        

### 4\. Pod networking is ready

*   Pod now has its own network namespace with eth0.
    
*   It can talk to other Pods/Services using:
    
    *   **Routing (overlay network)** → Flannel, Calico VXLAN.
        
    *   **Direct IPs (VPC-native)** → AWS VPC CNI.
        
    *   **BPF datapath** → Cilium.
        

### 5\. CNI DEL (teardown)

*   When Pod is deleted, kubelet calls the plugin with DEL.
    
*   Plugin cleans up routes, releases IP, deletes veth pair.
    

🔹 Visual Example (Calico / Flannel style)
==========================================

`   Pod netns (eth0: 10.244.1.5) <── veth ──> host netns (caliXYZ)                                           │                                           ├─ iptables / BPF rules                                           │                                       node eth0 (192.168.1.10)                                           │                                        Underlay network   `

🔹 Visual Example (AWS VPC CNI style)
=====================================

`   Pod netns (eth0: 10.0.1.25) ──> directly a VPC IP                                  (secondary IP from ENI)  Node eth0 (10.0.1.10 primary IP, 10.0.1.25 secondary IP)     │  AWS VPC subnet routing   `

🔹 Key Difference Across Plugins
================================

*   **Flannel/Calico (overlay mode):** Pods get IPs from cluster CIDR, traffic is encapsulated.
    
*   **AWS VPC CNI:** Pods get real VPC IPs, no encapsulation.
    
*   **Cilium (eBPF):** Programs dataplane using eBPF, no iptables.