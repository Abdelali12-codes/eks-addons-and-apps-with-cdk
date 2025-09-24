**1️⃣ Compute-Optimized (C family)**
------------------------------------

**Examples:** c6i, c7g, c5, c6g

*   **Designed for:** High CPU workloads.
    
*   **Characteristics:**
    
    *   More **vCPUs per dollar** than general purpose.
        
    *   Moderate memory.
        
    *   Fast processors (often latest Intel, AMD, or Graviton).
        
*   **Best for:**
    
    *   CPU-intensive tasks like data transformations, simulations, encoding, compression.
        
    *   Airflow: **workers running CPU-heavy DAGs**.
        
*   **Not ideal for:** Memory-heavy tasks or large in-memory processing.
    

**2️⃣ Memory-Optimized (R family)**
-----------------------------------

**Examples:** r6i, r7g, r5, r6g

*   **Designed for:** High memory workloads.
    
*   **Characteristics:**
    
    *   More **RAM per vCPU** than general-purpose or compute-optimized.
        
    *   Moderate CPU, so less ideal for pure CPU tasks.
        
*   **Best for:**
    
    *   In-memory databases, caching, analytics, ETL jobs that require large memory.
        
    *   Airflow: workers running **memory-heavy DAGs**, e.g., Pandas, Spark tasks.
        
*   **Not ideal for:** Pure CPU-bound workloads.
    

**3️⃣ General Purpose (M family)**
----------------------------------

**Examples:** m6i, m7g, m5, m6g

*   **Designed for:** Balanced CPU and memory.
    
*   **Characteristics:**
    
    *   Good **all-around performance**.
        
    *   Suitable for workloads that are neither CPU-heavy nor memory-heavy.
        
*   **Best for:**
    
    *   Web servers, small databases, backend services.
        
    *   Airflow: **scheduler, webserver, small workers with moderate load**.
        
*   **Not ideal for:** Extreme CPU-heavy or memory-heavy tasks.
    

### **Summary Table**

| Instance Type       | CPU      | Memory  | Use Case (Airflow)                             |
|--------------------|----------|--------|-----------------------------------------------|
| Compute-Optimized C | High     | Moderate | CPU-heavy workers, ETL transformations       |
| Memory-Optimized R  | Moderate | High    | Memory-heavy workers, big data processing    |
| General Purpose M   | Balanced | Balanced | Scheduler, Webserver, small-medium workers  |

### **Summary Table for EC2 Families**

| Family           | CPU       | Memory   | Storage        | Use Case                             |
|-----------------|----------|---------|---------------|-------------------------------------|
| M (General)      | Balanced | Balanced | EBS           | Scheduler, Webserver, balanced workers |
| C (Compute)      | High     | Moderate | EBS           | CPU-heavy workers                    |
| R (Memory)       | Moderate | High    | EBS           | Memory-heavy workers                 |
| I/D/H (Storage)  | Moderate | Moderate | Local NVMe/HDD | Data-intensive DAGs                  |
| T (Burstable)    | Low      | Moderate | EBS           | Dev/test Airflow                     |
| P/G/F (Accelerated)| GPU/FPGA | Varies  | Varies        | ML / graphics tasks                  |
| HPC/Inf          | Very High| High    | High-speed    | HPC or ML inference                  |


# Airflow Components and How They Use `airflow.cfg`

| Component                     | Uses `airflow.cfg` for…                                                                                   |
|-------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Webserver**                 | - Configures UI settings (`webserver` section)  <br> - Reads RBAC, proxy, and port settings  <br> - StatsD / metrics settings (`metrics` section) |
| **Scheduler**                 | - Reads core settings (`executor`, `dags_folder`, etc.)  <br> - Scheduler-specific settings (`scheduler` section)  <br> - StatsD / metrics |
| **Worker**                    | - Reads core (`executor`, `dags_folder`)  <br> - Celery or Kubernetes executor config (`celery`, `celery_kubernetes_executor`, `kubernetes_executor` sections)  <br> - Logging settings (`logging`) |
| **CLI / airflow commands**     | - Uses general core settings and connections to determine environment paths, logging, executor type, etc. |
| **Logging subsystem**          | - Uses `[logging]` and `[elasticsearch]` or `[elasticsearch_configs]` sections to configure log format, remote storage, retries |
| **KubernetesExecutor / Pod**  | - Reads `[kubernetes]` or `[kubernetes_executor]` sections for pod templates, namespaces, image, etc. |
| **Security (FAB / Kerberos)** | - `[fab]` and `[kerberos]` sections configure authentication and Kerberos tickets |
