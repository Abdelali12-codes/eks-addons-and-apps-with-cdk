Kubernetes API is organized into **groups** → each group has resources → resources have verbs (get, list, create, update, delete, watch, etc.).

Here’s the breakdown:

🔹 1. **Core API group** (also called "" → empty string)
--------------------------------------------------------

*   **Path**: /api/v1
    
*   **Namespace-scoped**: most of these
    
*   **Resources**:
    
    *   Pods (pods, pods/log, pods/exec, pods/portforward, pods/status)
        
    *   Services (services, services/status)
        
    *   ConfigMaps
        
    *   Secrets
        
    *   Endpoints
        
    *   PersistentVolumeClaims (persistentvolumeclaims, persistentvolumeclaims/status)
        
    *   PersistentVolumes (persistentvolumes)
        
    *   Namespaces (namespaces, namespaces/status, namespaces/finalize)
        
    *   Nodes (nodes, nodes/status, nodes/proxy, nodes/metrics)
        
    *   ServiceAccounts
        
    *   Events
        
    *   ReplicationControllers (replicationcontrollers, replicationcontrollers/status, replicationcontrollers/scale)
        

🔹 2. **apps**
--------------

*   **Path**: /apis/apps/v1
    
*   **Resources**:
    
    *   Deployments (deployments, deployments/status, deployments/scale)
        
    *   StatefulSets
        
    *   DaemonSets
        
    *   ReplicaSets
        
    *   ControllerRevisions
        

🔹 3. **batch**
---------------

*   **Path**: /apis/batch/v1
    
*   **Resources**:
    
    *   Jobs
        
    *   CronJobs
        

🔹 4. **autoscaling**
---------------------

*   **Path**: /apis/autoscaling/v1 (also v2, v2beta2 depending on cluster)
    
*   **Resources**:
    
    *   HorizontalPodAutoscaler (horizontalpodautoscalers)
        

🔹 5. **rbac.authorization.k8s.io**
-----------------------------------

*   **Path**: /apis/rbac.authorization.k8s.io/v1
    
*   **Resources**:
    
    *   Roles
        
    *   ClusterRoles
        
    *   RoleBindings
        
    *   ClusterRoleBindings
        

🔹 6. **apiextensions.k8s.io**
------------------------------

*   **Path**: /apis/apiextensions.k8s.io/v1
    
*   **Resources**:
    
    *   CustomResourceDefinitions (crds)
        

🔹 7. **apiregistration.k8s.io**
--------------------------------

*   **Path**: /apis/apiregistration.k8s.io/v1
    
*   **Resources**:
    
    *   APIService
        

🔹 8. **policy**
----------------

*   **Path**: /apis/policy/v1
    
*   **Resources**:
    
    *   PodDisruptionBudget (poddisruptionbudgets)
        

🔹 9. **networking.k8s.io**
---------------------------

*   **Path**: /apis/networking.k8s.io/v1
    
*   **Resources**:
    
    *   Ingresses
        
    *   IngressClasses
        
    *   NetworkPolicies
        

🔹 10. **storage.k8s.io**
-------------------------

*   **Path**: /apis/storage.k8s.io/v1
    
*   **Resources**:
    
    *   StorageClasses
        
    *   VolumeAttachments
        
    *   CSIStorageCapacity
        

🔹 11. **coordination.k8s.io**
------------------------------

*   **Path**: /apis/coordination.k8s.io/v1
    
*   **Resources**:
    
    *   Leases (used by leader election)
        

🔹 12. **certificates.k8s.io**
------------------------------

*   **Path**: /apis/certificates.k8s.io/v1
    
*   **Resources**:
    
    *   CertificateSigningRequests (CSRs)
        

🔹 13. **discovery.k8s.io**
---------------------------

*   **Path**: /apis/discovery.k8s.io/v1
    
*   **Resources**:
    
    *   EndpointSlices
        

🔹 14. **events.k8s.io**
------------------------

*   **Path**: /apis/events.k8s.io/v1
    
*   **Resources**:
    
    *   Events (new structured events API)
        

🔹 15. **admissionregistration.k8s.io**
---------------------------------------

*   **Path**: /apis/admissionregistration.k8s.io/v1
    
*   **Resources**:
    
    *   MutatingWebhookConfiguration
        
    *   ValidatingWebhookConfiguration
        

✅ To see **all API groups + resources in your cluster** dynamically, you can run:

`   kubectl api-resources   `

or grouped by API group:

`   kubectl api-resources --api-group=apps  kubectl api-resources --api-group=rbac.authorization.k8s.io   `