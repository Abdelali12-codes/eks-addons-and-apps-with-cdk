### **Description:**

While configuring **NGINX Stream** to proxy MySQL traffic (port **3306**) to a backend database, the NGINX service failed to start.

Relevant logs from journalctl -u nginx:

`   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok  nginx: [emerg] bind() to 0.0.0.0:3306 failed (13: Permission denied)  nginx: configuration file /etc/nginx/nginx.conf test failed  systemd[1]: nginx.service: Control process exited, code=exited, status=1/FAILURE   `

### **Configuration Context:**

*   NGINX was configured to use the **stream module** to proxy TCP connections for MySQL (port 3306).
    
*   upstream mysql\_backend { server data-dev-pandora-11.cluster-cw6sfpiklw3p.us-east-1.rds.amazonaws.com:3306;}server { listen 3306; proxy\_pass mysql\_backend;}
    
*   load\_module modules/ngx\_stream\_module.so;
    

### **Root Cause Analysis:**

1.  **Privileged Port Restriction**
    
    *   Port **3306** is below 1024, and binding to it requires elevated privileges.
        
    *   NGINX was running as a non-root user under systemd, causing a Permission denied error during the bind() system call.
        
2.  **SELinux Policy Enforcement**
    
    *   SELinux restricts which ports processes under specific contexts can bind to.
        
    *   NGINX runs under the httpd\_t SELinux type, which only permits ports like 80, 443, and 8080.
        
    *   Port 3306 was assigned to mysqld\_port\_t (MySQL), resulting in SELinux denying access even after privilege capabilities were granted.
        
3.  **Capability Adjustment Insufficient**
    
    *   setcap 'cap\_net\_bind\_service=+ep' /usr/sbin/nginx was applied to grant NGINX the ability to bind to privileged ports.
        
    *   However, SELinux continued to enforce port-type restrictions, preventing the service from starting.
        
4.  **Missing Module Loading**
    
    *   The ngx\_stream\_module was not loaded initially, which caused the stream configuration to be ignored.
        
    *   Adding load\_module modules/ngx\_stream\_module.so; in nginx.conf allowed NGINX to recognize and process the stream directives correctly.
        

### **Resolution Steps Implemented:**

1.  **Enabled the NGINX Stream Module**
    
    *   load\_module modules/ngx\_stream\_module.so;
        
2.  sudo nginx -t
    
3.  sudo setcap 'cap\_net\_bind\_service=+ep' /usr/sbin/nginx
    
4.  **Modified SELinux Port Context**
    
    *   sudo semanage port -m -t http\_port\_t -p tcp 3306
        
5.  sudo systemctl restart nginxsudo systemctl status nginx
    
6.  sudo semanage port -l | grep http\_port\_tOutput confirmed 3306 included under http\_port\_t.