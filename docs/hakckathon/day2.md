
This article details the deployment process of **AURA (AI Unified Response Agent)**, a sophisticated multi-agent system, to a production environment on **Vultr Cloud Compute**. This guide covers the full stack, including **Nginx** as a reverse proxy, **`systemd`** for service management, **Docker Compose** for core application orchestration, **Coral Protocol** for agent lifecycle management, and **PostgreSQL** as the database, all while adhering to best practices like non-root user execution.

This document serves as a comprehensive playbook, including troubleshooting steps encountered during development, to ensure a smooth and repeatable deployment.

## 🧠 Architectural Overview

AURA's production architecture is designed for robustness, scalability, and maintainability.

```mermaid
graph TD
    subgraph "Public Internet"
        User(User Browser)
    end

    subgraph "Vultr Cloud Compute (Ubuntu 22.04)"
        Nginx[Nginx Reverse Proxy]
        systemd[systemd Service Manager]
        Docker[Docker Compose]
        CoralServer(Coral Server Engine)
        CoralStudio(Coral Studio UI)
        PostgreSQL(PostgreSQL Database)
        Agent1(Identifier Agent)

```
---
# Deploying a Robust Multi-Agent AI System to Vultr: A Step-by-Step Guide

## From Local Development to Enterprise-Grade Cloud Deployment with Aura

**By Nabil MABROUK**

## Introduction

This guide documents the journey of deploying Aura, a sophisticated multi-agent AI system, to a production-grade environment on Vultr Cloud. Aura is designed to revolutionize enterprise operations by orchestrating specialist AI agents to diagnose problems, fetch procedures, and guide technicians, turning chaos into controlled, auditable action.

This guide is intended to be a complete blueprint for re-deploying the project from scratch, covering system setup, dependency management, service orchestration, networking, and critical troubleshooting steps encountered during the hackathon. We'll leverage Docker, Nginx, systemd, Coral Protocol, and PostgreSQL to build a robust, scalable, and professional architecture.

## Architecture Overview

Our final architecture is a hybrid system, strategically leveraging the strengths of different tools for optimal performance and manageability:

1.  **Nginx (Reverse Proxy):** The public entry point, routing traffic to the correct internal services.
2.  **Docker Compose (Container Orchestration):** Manages the core Django application (`Supervisor`), its background worker (`Celery Worker`), and the message broker (`Redis`, `PostgreSQL`).
3.  **systemd (Service Management):** Ensures the `Coral Server` (agent orchestrator) and `Coral Studio` (UI) run persistently in the background.
4.  **Coral Protocol (Agent Orchestration):** Launched by `systemd`, it is responsible for dynamically spawning and managing our three specialist FastAPI agents directly on the host server.
5.  **FastAPI Agents:** Lightweight microservices (`Identifier`, `Procedure`, `Summarizer`) performing specific AI tasks.
6.  **PostgreSQL:** The robust relational database for the Django application.
7.  **Vultr Cloud:** The underlying infrastructure hosting everything.

```
       Internet
          |
          v
+-----------------------+
|  Vultr IP (Port 80)   |
|     (ufw Firewall)    |
+-----------+-----------+
            |
            v
+-----------------------+
|    Nginx (Port 80)    |
|   (Reverse Proxy)     |
+-----------+-----------+
            |
            +----- 8000 (HTTP) ----> +------------------------+
            |                        |  Docker Container:     |
            |                        |  Aura Supervisor (Django)  |
            |                        +------------------------+
            |                                  |
            +----- 3000 (HTTP) ----> +------------------------+
            |                        |  systemd:              |
            |                        |  Coral Studio (UI)     |
            |                        +------------------------+
            |                                  |
            +----- 5555 (WebSocket) -> +------------------------+
            |                        |  systemd:              |
            |                        |  Coral Server (Engine) | ---- Spawns Agents Directly ----> +--------------------+
            |                        +------------------------+                                  | FastAPI Agents:    |
            |                                  |                                                   | - Identifier (8001)|
            +----- (Internal) ------>+------------------------+                                  | - Procedure (8002) |
            |                        |  Docker Container:     |                                   | - Summarizer (8003)|
            |                        |  Celery Worker         |                                   +--------------------+
            |                        +------------------------+
            |                                  |
            +----- (Internal) ------>+------------------------+
                                     |  Docker Container:     |
                                     |  Redis (Broker)        |
                                     +------------------------+
                                                 |
                                                 +----- (Internal) ------>+------------------------+
                                                                         |  Docker Container:     |
                                                                         |  PostgreSQL (Database) |
                                                                         +------------------------+
```

## Prerequisites

Before you begin, ensure you have:

*   **Vultr Account:** With sufficient credits (your hackathon credits are more than enough).
*   **GitHub Repository:** Your Aura project code should be pushed to a public or private GitHub repository.
*   **Snowflake Account:** With a database and a `PROCEDURES` table set up (as discussed previously).
*   **SSH Client:** On your local machine (e.g., Git Bash on Windows, Terminal on macOS/Linux).

## Step-by-Step Deployment Guide

### 1. Provision Your Vultr Server

1.  **Log in** to your Vultr account.
2.  Go to **Deploy Server**.
3.  Choose **Cloud Compute**.
4.  **Server Type:** **Ubuntu 22.04 LTS**.
5.  **Server Size:** At least **2 vCPUs** and **2 GB RAM** (e.g., the $12/month option).
6.  Choose a **Server Location** (e.g., Paris).
7.  Provide a **Hostname** and **Label** (e.g., `aura-server`).
8.  Click **"Deploy Now"**. Note down the **IP Address** and **root password**.

### 2. Connect and Install Base Dependencies

SSH into your new server.

```bash
ssh root@[YOUR_VULTR_IP_ADDRESS]
```
Enter the password when prompted.

Now, install all necessary system packages:

```bash
# Update and upgrade existing packages
apt update && apt upgrade -y

# Install Git
apt install git -y

# Install Docker and Docker Compose
apt install docker.io -y
apt install docker-compose -y

# Install Node.js (v20.x from NodeSource for Coral Studio)
curl -sL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g yarn # Install yarn globally

# Install Java (JDK 21 for Coral Server)
apt install -y default-jdk

# Install Python venv (if not already installed)
apt install python3-venv -y

# Install Nginx (for reverse proxy)
apt install nginx -y

# Install PostgreSQL (for database)
apt install postgresql postgresql-contrib -y

# Install `ufw` (Uncomplicated Firewall)
apt install ufw -y
```

### 3. PostgreSQL Database Setup

We'll create a dedicated user and database for Django.

1.  Switch to the `postgres` user:
    ```bash
    sudo -i -u postgres
    ```
2.  Access the PostgreSQL prompt:
    ```bash
    psql
    ```
3.  Create a new database user (replace `aura_user` and `your_db_password`):
    ```sql
    CREATE USER aura_user WITH PASSWORD 'your_db_password';
    ```
4.  Create the database (replace `aura_db`):
    ```sql
    CREATE DATABASE aura_db WITH OWNER aura_user;
    ```
5.  Grant all privileges on the database to the user:
    ```sql
    GRANT ALL PRIVILEGES ON DATABASE aura_db TO aura_user;
    ```
6.  Exit `psql` and then the `postgres` user:
    ```sql
    \q
    exit
    ```

### 4. Clone Your Code and Setup Python Environment

Navigate to the root directory and clone your project.

```bash
cd /root/

# Clone your main project repository
git clone https://github.com/your-username/Aura.git # Ensure 'Aura' matches your repo name (case-sensitive)

# Clone Coral Protocol repositories (external dependencies)
git clone https://github.com/Coral-Protocol/coral-server.git
git clone https://github.com/Coral-Protocol/coral-studio.git
```

Now, set up your Python virtual environment and install all dependencies:

```bash
cd /root/Aura/ # Go to your project root

# Create the virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install all Python dependencies into the venv
# Note: psycopg2-binary for PostgreSQL is added here.
pip install -r ./Aura/requirements.txt
pip install -r ./agents/identifier_agent/requirements.txt
pip install -r ./agents/procedure_agent/requirements.txt
pip install -r ./agents/summarizer_agent/requirements.txt

# Deactivate (optional, but good practice)
deactivate
```

### 5. Server-Side Configuration

This is where you update files for the production environment.

1.  **Django Settings (`/root/Aura/Aura/settings.py`):**
    ```python
    # ...
    DEBUG = False # IMPORTANT: Set to False in production
    ALLOWED_HOSTS = ['YOUR_VULTR_IP_ADDRESS'] # Add your server's public IP

    # Database configuration for PostgreSQL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2", # Change this line
            "NAME": "aura_db",      # Your PostgreSQL database name
            "USER": "aura_user",    # Your PostgreSQL database user
            "PASSWORD": "your_db_password", # Your PostgreSQL password
            "HOST": "postgres",     # Docker Compose service name for PostgreSQL
            "PORT": "5432",
        }
    }
    # ...
    ```

2.  **Snowflake `.env` file (`/root/Aura/agents/procedure_agent/.env`):**
    This file is not in Git. Create it on the server:
    ```bash
    nano /root/Aura/agents/procedure_agent/.env
    ```
    Paste your Snowflake credentials:
    ```
    SNOWFLAKE_USER="YOUR_SNOWFLAKE_USERNAME"
    SNOWFLAKE_PASSWORD="YOUR_SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT="YOUR_ACCOUNT_IDENTIFIER"
    SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
    SNOWFLAKE_DATABASE="DEMO_DB"
    SNOWFLAKE_SCHEMA="PUBLIC"
    ```

3.  **Coral Server `application.yaml` (`/root/coral-server/src/main/resources/application.yaml`):**
    This file defines how Coral launches your agents.
    ```bash
    nano /root/coral-server/src/main/resources/application.yaml
    ```
    **Replace its content with this definitive version:**
    ```yaml
    applications:
      - id: "aura-app"
        name: "AURA Supervisor Application"
        privacyKeys: ["default-key"]

    registry:
      aura-identifier-agent:
        options: []
        runtime:
          type: "executable"
          command: ["bash", "-c", "cd /root/Aura/agents/identifier_agent && source /root/Aura/venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8001"]

      aura-procedure-agent:
        options: []
        runtime:
          type: "executable"
          command: ["bash", "-c", "cd /root/Aura/agents/procedure_agent && source /root/Aura/venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8002"]
          environment:
            - name: "HOME"
              value: "/root" # On Linux, use HOME for the home directory

      aura-summarizer-agent:
        options: []
        runtime:
          type: "executable"
          command: ["bash", "-c", "cd /root/Aura/agents/summarizer_agent && source /root/Aura/venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8003"]
    ```

4.  **Coral Studio `vite.config.js` (`/root/coral-studio/vite.config.js`):**
    This ensures the UI builds correctly for proxying.
    ```bash
    nano /root/coral-studio/vite.config.js
    ```
    **Add the `base` property:**
    ```javascript
    import { sveltekit } from '@sveltejs/kit/vite';
    import { defineConfig } from 'vite';

    export default defineConfig({
    	base: '/studio/', // Add this line
    	plugins: [sveltekit()]
    });
    ```

### 6. Configure Nginx and Firewall (`ufw`)

1.  **Nginx Configuration (`/etc/nginx/sites-available/aura_proxy`):**
    ```bash
    nano /etc/nginx/sites-available/aura_proxy
    ```
    **Replace its content with this full, correct version:**
    ```nginx
    server {
        listen 80;
        server_name YOUR_VULTR_IP_ADDRESS;

        access_log /var/log/nginx/aura_access.log;
        error_log /var/log/nginx/aura_error.log;

        # Route for the main Django Supervisor App
        location / {
            proxy_pass http://127.0.0.1:8000; # Forwards to Gunicorn
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Route for the Coral Studio UI
        location /studio/ {
            proxy_pass http://127.0.0.1:3000/; # Forwards to the Vite preview server
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Route for the Socket.IO real-time communication (goes to Coral Server)
        location /socket.io/ {
            proxy_pass http://127.0.0.1:5555; # Forwards to Coral Server
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade"; # Capital 'U' is important
            proxy_set_header Host $host;
        }
    }
    ```
    Enable and restart Nginx:
    ```bash
    ln -s /etc/nginx/sites-available/aura_proxy /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    ```

2.  **`ufw` Firewall Rules:**
    Allow necessary ports through the local firewall.
    ```bash
    ufw allow 22/tcp # For SSH
    ufw allow 80/tcp # For Nginx (HTTP)
    ufw allow 443/tcp # For Nginx (HTTPS, if you set it up later)
    ufw allow 5555/tcp # For direct Coral Server communication (from Studio UI)
    ufw enable # Enable the firewall if not already active. Confirm if prompted.
    ```

### 7. Configure `systemd` Services

Create service files to manage `coral-server` and `coral-studio`.

1.  **`coral-server.service` (`/etc/systemd/system/coral-server.service`):**
    ```bash
    nano /etc/systemd/system/coral-server.service
    ```
    ```ini
    [Unit]
    Description=Coral Protocol Server Engine
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/root/coral-server
    ExecStart=/root/coral-server/gradlew run
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

2.  **`coral-studio.service` (`/etc/systemd/system/coral-studio.service`):**
    ```bash
    nano /etc/systemd/system/coral-studio.service
    ```
    ```ini
    [Unit]
    Description=Coral Studio UI - Production Preview
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/root/coral-studio
    ExecStart=/usr/bin/npm run preview -- --host 127.0.0.1 --port 3000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    Enable and start the services:
    ```bash
    systemctl daemon-reload
    systemctl start coral-server coral-studio
    systemctl enable coral-server coral-studio
    systemctl status coral-server coral-studio
    ```

### 8. Final Docker Compose Configuration and Launch

1.  **`docker-compose.yml` (`/root/Aura/docker-compose.yml`):**
    ```bash
    nano /root/Aura/docker-compose.yml
    ```
    **Replace its content with this version:**
    ```yaml
    version: '3.8'

    services:
      # The PostgreSQL database service
      postgres:
        image: postgres:16-alpine # Using Alpine for smaller image
        environment:
          POSTGRES_DB: aura_db
          POSTGRES_USER: aura_user
          POSTGRES_PASSWORD: your_db_password # Use your password here
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data/ # Persistent data volume

      # The Redis message broker
      redis:
        image: "redis:alpine"
        ports:
          - "6379:6379"

      # The Django Supervisor Service
      supervisor:
        build:
          context: ./Aura
          dockerfile: ../Dockerfile.supervisor
        ports:
          - "8000:8000"
        command: ["/app/startup.sh"] # Runs migrations and gunicorn
        volumes:
          - ./database:/app/database # For shared SQLite (will switch to Postgres)
        environment:
          - DJANGO_SETTINGS_MODULE=Aura.settings
          - CELERY_BROKER_URL=redis://redis:6379/0
          - CELERY_RESULT_BACKEND=redis://redis:6379/0
          # Ensure correct DB settings (match Django settings.py)
          - POSTGRES_DB=aura_db
          - POSTGRES_USER=aura_user
          - POSTGRES_PASSWORD=your_db_password
          - POSTGRES_HOST=postgres # Service name in Docker Compose
          - POSTGRES_PORT=5432
        extra_hosts:
          - "host.docker.internal:host-gateway" # For contacting host agents
        depends_on:
          - redis
          - postgres # Depends on postgres for DB

      # The Celery Worker Service
      celery_worker:
        build:
          context: ./Aura
          dockerfile: ../Dockerfile.supervisor
        command: ["sh", "-c", "celery -A Aura worker -l info"] # Removed migrate here, startup.sh handles it
        volumes:
          - ./database:/app/database
        environment:
          - DJANGO_SETTINGS_MODULE=Aura.settings
          - CELERY_BROKER_URL=redis://redis:6379/0
          - CELERY_RESULT_BACKEND=redis://redis:6379/0
          - POSTGRES_DB=aura_db
          - POSTGRES_USER=aura_user
          - POSTGRES_PASSWORD=your_db_password
          - POSTGRES_HOST=postgres
          - POSTGRES_PORT=5432
        extra_hosts:
          - "host.docker.internal:host-gateway"
        depends_on:
          - redis
          - postgres

    volumes:
      postgres_data: # Define the named volume for PostgreSQL data
    ```

2.  **Launch Docker Compose:**
    ```bash
    cd /root/Aura
    docker-compose down # Clean up any old containers
    docker-compose up --build -d # Build and run everything in detached mode
    ```

### Troubleshooting Guide (Common Issues & Solutions)

This section summarizes the problems encountered and their resolutions.

*   **`bash: line 1: No such file or directory` (venv activation/`cd` errors):**
    *   **Cause:** Incorrect relative paths in `application.yaml` or `startup.sh`, or missing `venv` on server, or case-sensitivity issues.
    *   **Solution:** Ensure `venv` is created (`python3 -m venv venv`) and `pip install -r` is run in it on the server. Use **absolute paths** or carefully verified **relative paths from `WORKDIR`** in `application.yaml`. Ensure correct case (`/root/Aura/` vs `/root/aura/`).

*   **`Unknown section 'unit'. Ignoring.` (systemd service file):**
    *   **Cause:** Hidden characters or incorrect formatting at the start of the `systemd` `.service` file.
    *   **Solution:** Delete and recreate the `.service` file cleanly using `nano`. Use `systemctl daemon-reload` after edits.

*   **`Unknown command: --config` (Coral Server startup):**
    *   **Cause:** The `coral-server` (Gradle version) does not accept a `--config` flag. It expects `application.yaml` in `src/main/resources`.
    *   **Solution:** Remove `--args="--config ..."` from `ExecStart` in `coral-server.service`. Ensure `WorkingDirectory=/root/coral-server` is set in the service file.

*   **`ERROR: [Errno 98] address already in use` (Agents on 8001/8002/8003):**
    *   **Cause:** Both Docker Compose and the Coral Server were trying to launch agents on the same ports, leading to a conflict.
    *   **Solution:** Remove agent definitions from `docker-compose.yml`. Let **ONLY Coral Server** manage spawning agents directly on the host.

*   **`Failed to load resource: net::ERR_CONNECTION_REFUSED` / `502 Bad Gateway` (Browser/Nginx to Services):**
    *   **Cause:** Firewall (`ufw`) blocking incoming public traffic, or Nginx not correctly proxying requests, or the backend service not listening on the correct IP/Port.
    *   **Solution:**
        *   **`ufw`:** Add explicit `ufw allow` rules for all public-facing ports (80, 443, 5555 for Coral Server direct connection).
        *   **Nginx:** Ensure `proxy_pass` points to correct `127.0.0.1:PORT` or `host.docker.internal:PORT`. Add `proxy_set_header` for `Host`, `Upgrade`, `Connection`. Use correct `proxy_pass` pathing (e.g., `proxy_pass http://127.0.0.1:5555/socket.io/` for `socket.io` paths).
        *   **Node/Vite:** Ensure `npm run dev` or `npm run preview` has `--host 127.0.0.1` or `--host 0.0.0.0` if Nginx is proxying.

*   **`Form data requires "python-multipart" to be installed.`:**
    *   **Cause:** Missing `python-multipart` in an agent's `requirements.txt` when handling `UploadFile` in FastAPI.
    *   **Solution:** Add `python-multipart` to the agent's `requirements.txt` file.

*   **`RuntimeError: Could not determine home directory.` (Snowflake Connector):**
    *   **Cause:** Python's `snowflake-connector-python` needing a `HOME` (Linux) or `USERPROFILE` (Windows) environment variable that isn't set in the subprocess.
    *   **Solution:** Add `environment:` block to the agent's definition in `application.yaml`:
        ```yaml
        environment:
          - name: "HOME"
            value: "/root" # Or "%USERPROFILE%" on Windows
        ```

*   **`The engine "node" is incompatible with this module. Expected version ">= 18". Got "12.x.x"`:**
    *   **Cause:** Default Node.js package from Ubuntu is outdated.
    *   **Solution:** Use NodeSource repository to install a modern Node.js version (e.g., 20.x).

*   **`vite: not found` / `sh: 1: vite: not found` (Coral Studio startup):**
    *   **Cause:** Local Node.js project dependencies (`vite`) not installed on the server.
    *   **Solution:** Run `npm install` (or `yarn install`) inside the `coral-studio` directory on the server.

*   **`django.db.utils.OperationalError: FATAL: password authentication failed for user "aura_user"`:**
    *   **Cause:** Incorrect PostgreSQL username, password, or host in Django `settings.py` or `docker-compose.yml`. Or `pg_hba.conf` issue (less likely if within Docker network).
    *   **Solution:** Double-check credentials. Ensure `POSTGRES_HOST` is `postgres` (the service name).

### Future Enhancements (Beyond Hackathon Scope)

1.  **HTTPS (SSL/TLS):** Essential for production. Obtain a free SSL certificate (e.g., from Let's Encrypt) and configure Nginx to serve traffic over HTTPS (port 443).
2.  **Non-Root User:** For security, avoid running services as the `root` user. Create dedicated Linux users and configure `systemd` services and Docker containers to run under these less privileged accounts.
3.  **Observability:** Implement logging (e.g., ELK stack), monitoring (e.g., Prometheus/Grafana), and alerting for a real production environment.
4.  **Persistent Agent Storage:** If agents have mutable state, consider persistent volumes or object storage for them.