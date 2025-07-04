
# Aura Cloud: The Centralized Expert Agent

<div align="center">
  <img src="https://i.imgur.com/u1mJ2pC.png" alt="Aura Cloud Cover Image" width="700"/>
</div>

**A submission for the [RAISE YOUR HACK](https://lablab.ai/event/raise-your-hack) Hackathon - Vultr Track.**

Aura is a cloud-native, agentic system that provides **real-time visual intelligence** to on-site technicians. Deployed on a professional stack on **Vultr**, it uses a hybrid AI pipeline to analyze a technician's live video feed, deliver interactive repair guidance, and autonomously manage the entire service workflow, turning every junior technician into your best troubleshooter.

---

## 🎥 Demo Video

<div align="center">

[](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

**Click the thumbnail above to watch our 3-minute live demonstration.**
</div>

---

## 🎯 The Problem

In mission-critical industries like energy, manufacturing, and telecommunications, field service operations are plagued by inefficiency. When equipment fails, technicians on-site often lack immediate access to expert knowledge. This leads to:

*   **Costly Downtime:** Every minute spent diagnosing a problem is a direct financial loss. A single hour of downtime can cost a factory thousands.
*   **Knowledge Gaps:** The expertise of senior engineers isn't scalable. They can't be everywhere at once, leaving junior technicians to rely on cumbersome paper manuals.
*   **Inefficient Reporting:** Technicians spend up to 40% of their time on administrative tasks and paperwork instead of value-adding repairs.

---

## ✨ Our Solution: The Aura Agent

Aura Cloud tackles these problems by providing a single, powerful AI brain hosted on Vultr that any technician can access from any device with a web browser. It's not just a tool; it's an **agentic co-pilot** that sees what the technician sees and orchestrates the entire service workflow.

### Key Features

*   **Centralized Live Vision:** Technicians stream their camera feed to Vultr, which handles the heavy AI processing (**YOLOv8 object detection**) to identify machinery and components in real-time.
*   **Hybrid AI-Powered Knowledge:** A sophisticated Retrieval-Augmented Generation (RAG) pipeline provides expert guidance.
    *   **Vultr Serverless Inference:** Hosts a dedicated embedding model for scalable, managed knowledge vectorization.
    *   **Groq API + Llama 3.1:** Delivers lightning-fast, state-of-the-art conversational responses based on technical manuals.
*   **End-to-End Agentic Workflow:** Aura can manage a repair ticket from start to finish, interacting with other enterprise systems (e.g., Jira, Snowflake) to automate administrative tasks.
*   **Automated Reporting:** The agent acts as a scribe, documenting the entire process to generate service reports instantly, freeing up technicians to focus on their core job.
*   **Interoperable by Design (MCP):** Built on the **Model Context Protocol (MCP)**, Aura exposes its capabilities so other enterprise agents can discover and collaborate with it programmatically.

---

## 🤖 Architecture: A Modern, Cloud-Native Stack

Aura Cloud is built as a professional, containerized application deployed entirely on Vultr infrastructure. This architecture is designed for scalability, reliability, and interoperability.

<div align="center">
  <img src="https://i.imgur.com/jA7B3tF.png" alt="Aura Cloud Architecture Diagram" width="800"/>
</div>

### Meeting the Hackathon Requirements

*   **Core Requirement (Groq + Llama):** The primary RAG-based conversational logic is powered by the **Groq API** and **Llama 3.1**.
*   **Vultr Track (Deployment):** The entire stack is containerized with **Docker** and deployed on a **Vultr VM**, powered by a **Uvicorn** ASGI server and an **Nginx** reverse proxy.
*   **Vultr Track (Partner Tech):** We strategically use **Vultr Serverless Inference** for our embedding model, demonstrating a hybrid AI approach that leverages the best of Vultr's native platform.
*   **Vultr Track (Partner Tech):** The entire application is designed to be wrapped in an **MCP** server, making it a true, forward-looking enterprise agent that adheres to emerging interoperability standards.

---

## 🛠️ Tech Stack

*   **Cloud Hosting:** Vultr (VM, Serverless Inference)
*   **Backend:** Django, Django REST Framework, Django Channels
*   **ASGI Server:** Uvicorn
*   **Frontend:** HTML5, TailwindCSS, JavaScript
*   **Real-Time Comms:** WebRTC, WebSockets
*   **Conversational AI:** Groq API, Llama 3.1
*   **Computer Vision:** YOLOv8, OpenCV
*   **RAG Pipeline:**
    *   **Embeddings:** Vultr Serverless Inference
    *   **Vector Store:** Qdrant / Faiss (in Docker)
*   **Agent Protocol:** Model Context Protocol (MCP)
*   **Deployment:** Docker, Docker Compose, Nginx

---

## 🚀 Getting Started & Local Development

This project is fully containerized for easy and consistent setup.

### Prerequisites

*   Docker and Docker Compose
*   A Vultr account with a deployed Serverless Inference embedding model.
*   A Groq API Key.
*   A webcam.

### Local Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Nabil-Mabrouk/aura.git
    cd aura-cloud
    ```

2.  **Set Up Environment Variables:**
    Create a file named `.env` in the project root by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file and add your secret keys:
    ```
    GROQ_API_KEY="gsk_YourGroqApiKeyHere"
    VULTR_INFERENCE_URL="https://your-region.vultr.com/v1/inference/your-endpoint-id"
    ```

3.  **Build and Run with Docker Compose:**
    This single command will build the containers, install dependencies, and start the application.
    ```bash
    docker-compose up --build
    ```

4.  **Access the Application:**
    Open your web browser and navigate to:
    **`https://localhost:8000`**
    *(Note the `https`)*

    Your browser will trust the connection because of the `mkcert` certificate. You can now grant camera permissions and use the app.

---

## 👨‍💻 About the Developer

Aura Cloud was designed and built by [Your Name] as a solo project for the RAISE YOUR HACK hackathon.

*   **GitHub:** [@Nabil-Mabrouk](https://github.com/Nabil-Mabrouk)
*   **LinkedIn:** [linkedin.com/in/your-linkedin-profile](https://www.linkedin.com/in/your-linkedin-profile)
