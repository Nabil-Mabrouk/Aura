# Aura's Genesis: From Concept to a Local Multi-Agent System on Day 1

## A Deep Dive into Strategic Choices, Rapid Development, and Troubleshooting at RAISE Your HACK

**By Nabil Mabrouk**

## Introduction

Day 1 of the **RAISE Your HACK** hackathon has just concluded, and the progress is exhilarating! As a solo developer on the **Vultr Track** ("Agentic Workflows for the Future of Work"), my objective is to build **AURA (AI Unified Response Agent)**. Aura aims to revolutionize enterprise operations by orchestrating specialist AI agents to diagnose problems, fetch procedures, and guide technicians, transforming chaos into controlled, auditable action.

This first day was relentlessly focused on laying a robust, multi-service architectural foundation. The goal was ambitious: to achieve a fully functional, local multi-agent system, complete with core integrations and a seamless communication flow. I'm proud to report that this demanding target was met, showcasing the power of strategic planning and rapid problem-solving.

## Strategic Foundation: The "Why" Behind the Stack

Before a single line of code was written, critical architectural decisions were made to ensure feasibility within a 4-day sprint while aiming for a production-grade future.

### Project Feasibility & Scope Management:

*   **Specific Problem, Focused Demo:** Instead of broadly tackling "enterprise ops," Aura's initial scope was narrowed to a clear pain point: diagnosing and guiding technicians through hardware repair. The demo would focus on a single, relatable scenario (e.g., a GPU replacement), allowing deep implementation rather than shallow breadth.
*   **MVP First, "Wow" Later:** The priority was a stable, end-to-end functional core. Advanced features like real-time video analysis and speech interaction, while crucial for the "wow" factor, were deliberately deferred as stretch goals, ensuring the primary objective was met.
*   **GitHub Issues as a Roadmap:** A detailed GitHub Issue track was created, breaking down the entire project into manageable, sequential tasks. This disciplined approach kept the development focused and provided a clear visual progress tracker.

### Tool Selection: The "Right Tool for the Right Job":

*   **Django (Aura Supervisor):** Chosen for its rapid web development capabilities, robust ORM (Object-Relational Mapper) for quick database model creation, and battle-tested framework for managing the core application logic and web UI.
*   **FastAPI (Specialist Agents):** Selected for its speed, lightweight nature, and strong support for creating asynchronous API endpoints with automatic data validation (via Pydantic). It's perfect for building lean microservices.
*   **Snowflake (Enterprise Data Source):** A key technology partner, chosen to demonstrate fetching authoritative, structured business procedures from a real enterprise data warehouse, avoiding "guessing" by the AI.
*   **Coral Protocol (Agent Orchestration & Discovery):** A crucial technical partner. Coral was selected not just as a dependency, but as the *orchestration layer* for the multi-agent system. It aligns directly with the "Agentic Workflows" theme by enabling dynamic agent discovery and lifecycle management.
*   **Docker (Future Containerization):** Although full containerization of the entire stack was planned for later days, all development was done with Docker compatibility in mind, ensuring a smooth transition to a containerized environment.

## The Day 1 Development Sprint: Building the Local Ecosystem

Day 1 was a whirlwind of coding, focused on bringing the core multi-agent system to life locally.

### 1. The Aura Supervisor: Django's Foundation

*   **Project Initialization:** A new Django project (`Aura`) and a core application (`core`) were set up.
*   **Data Models:** `Job` and `JobLog` models were defined in `core/models.py` to track the state and history of each operational task. This forms the central data repository for the supervisor.
*   **Core Workflow Logic (`core/tasks.py` and `core/views.py`):**
    *   Initially, a placeholder `run_job_workflow_task` function was created in `core/tasks.py` (which would later become a Celery task). This function outlined the multi-step agentic process, making calls to *mocked* agent services.
    *   The `create_and_run_job` view in `core/views.py` was set up to trigger this workflow in a background thread, ensuring the web request remained responsive.
*   **Basic Web UI & Live Logging:**
    *   `job_list.html` and `job_detail.html` templates were created with Tailwind CSS for a clean, functional interface.
    *   Crucially, `job_detail.html` included JavaScript to poll a Django API endpoint (`/app/api/job/<uuid:job_id>/log/`) every 1.5 seconds, populating a "live log" in real-time. This provided instant visual feedback on the agent's progress, a key demo feature.
*   **URL Routing:** Django's `urls.py` was configured to namespace the `core` app (e.g., `core:job_list`) for clean URL management. A separate `landing` app was also created for the homepage, redirecting users to the main supervisor app.

### 2. The Specialist Agents: FastAPI Microservices

To demonstrate true agentic separation, three independent FastAPI microservices were built:

*   **Identifier Agent (Port 8001):** Its `main.py` defined a `/identify` endpoint. For Day 1, it simply returned hardcoded component identification data.
*   **Procedure Agent (Port 8002):** Its `main.py` defined a `/get_procedure` endpoint. It returned hardcoded procedural steps and safety warnings. This agent was designated for Snowflake integration later.
*   **Summarizer Agent (Port 8003):** Its `main.py` defined a `/summarize` endpoint. It returned a hardcoded summary of a job.

Each agent used `uvicorn` to serve its FastAPI application. The Django Supervisor's `core/services.py` was then updated to make direct `requests.post()` calls to these local agent endpoints, establishing the inter-agent communication.

### 3. Enterprise Data Integration: Snowflake

The `Procedure Agent` was then upgraded to connect to a real enterprise database.

*   **Snowflake Setup:** A `PROCEDURES` table was created in the Snowflake web UI, designed to store structured operational steps and safety warnings using Snowflake's `VARIANT` data type (ideal for JSON). Sample data for a "NVIDIA RTX 4090 GPU" was inserted.
*   **Python Connector:** The `snowflake-connector-python` library was installed.
*   **Secure Credentials:** A `.env` file was created in the `procedure_agent` directory to securely store Snowflake credentials.
*   **Agent Logic Update:** The `procedure_agent/main.py` was modified to use these credentials, connect to Snowflake, and query the `PROCEDURES` table based on the component name, returning live data instead of hardcoded responses.

### 4. Agent Orchestration: Coral Protocol (Local Setup)

The final, sophisticated step on Day 1 was integrating Coral Protocol as the agent orchestrator.

*   **`application.yaml`:** A central `application.yaml` file was created in the project root. This file registered the three specialist agents with the Coral Protocol, defining their names, endpoints (8001, 8002, 8003), and capabilities (e.g., `vision:object_detection`).
*   **Coral Server (`./gradlew run`):** The Coral Protocol Server was run from its cloned GitHub source (using `./gradlew run`), which reads the `application.yaml` to understand the agent ecosystem.
*   **Coral Studio UI (`npm run dev`):** The Coral Studio web UI was launched locally, designed to connect to the `coral-server` and visually manage agent sessions.
*   **Supervisor Interaction:** The Django Supervisor was updated to interact with the Coral system. Initially, attempts were made to programmatically create sessions via a Coral Python SDK, but this was refined to a more robust approach where the Supervisor makes direct calls to the agent endpoints *after* the Coral Server has launched them (triggered by manually creating a session in the Coral Studio UI). This allowed demonstration of Coral's orchestration without complex asynchronous client logic in Django.

## Day 1 Troubleshooting: Navigating the Hurdles

Day 1 was not without its challenges, primarily related to environment setup and inter-service communication. Each problem provided valuable learning.

*   **`name 'time' is not defined`**: A simple Python `ImportError` in `core/views.py` due to a missing `import time` statement, quickly resolved.
*   **`NoReverseMatch at /app/job/new/`**: Django error stemming from URL namespacing. The `redirect()` calls in `core/views.py` needed to be updated from `redirect('job_detail', ...)` to `redirect('core:job_detail', ...)`.
*   **`Form data requires "python-multipart" to be installed.`**: An `RuntimeError` in FastAPI agents when handling `UploadFile` types. Resolved by adding `python-multipart` to the `identifier_agent`'s `requirements.txt`.
*   **`RuntimeError: Could not determine home directory.` (Snowflake Connector):** A specific issue with the `snowflake-connector-python` failing to find the user's home directory in a non-interactive subprocess environment. Solved by adding an `environment:` block to the `procedure_agent`'s definition in `application.yaml`, explicitly setting `HOME` (or `USERPROFILE` on Windows) to `/root`.
*   **`UnknownPropertyException at PROJECT_DIR` / `Property 'options' is required` (Coral `application.yaml` parsing):** Early configuration errors in `application.yaml`. `PROJECT_DIR` was not a valid top-level key; `options: []` was a mandatory field for each agent registry entry. Resolved by adhering strictly to Coral's YAML schema.
*   **`bash: ... No such file or directory` (Agent launch via `application.yaml`):** When `coral-server` tried to launch agents, the `bash` command couldn't find the `venv` or agent directories. This was due to incorrect **relative paths** (`../Aura/venv/bin/activate`) from the `coral-server`'s working directory or **case-sensitivity** (e.g., `aura` vs `Aura`) on Linux. The solution involved ensuring all paths in `application.yaml` were **absolute paths** or perfectly matching **case-sensitive relative paths** from the `coral-server` root. Additionally, ensuring the `venv` was actually created and populated on the server was a critical missing step.

By tackling these challenges head-on, Day 1 concluded with a robust, locally operating, multi-agent Aura system.

## Outlook for Day 2: Advanced AI & Cloud Deployment

With a solid foundation laid, Day 2 will be focused on:

*   **Mandatory Groq/Llama Integration:** Implementing a new "Command Agent" to use Groq's Llama model for real-time natural language understanding and speech-to-text.
*   **Advanced AI Features:** Beginning integration of real-time video object detection (YOLOv8) and text-to-speech for conversational interaction.
*   **Full Cloud Deployment:** Containerizing the core application with Docker Compose and deploying the entire system (including Coral Protocol components) to Vultr Cloud, using Nginx for routing and systemd for process management.

The journey continues to transform Aura into a truly intelligent and impactful solution for the future of work.