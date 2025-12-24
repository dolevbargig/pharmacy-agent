# 🏥 Pharmacy AI Agent

An intelligent AI assistant that provides pharmacy medication and prescription information through multi-step flows using tools, with clear safety boundaries.

## 📋 Overview

The pharmacy AI Agent helps pharmacy customers get information about medications and prescription requirements.
It provides factual information only while avoiding medical advice or diagnoses.
The agent answers follow-up questions while maintaining conversation context. 
It supports both English and Hebrew, based on the user's choice.

## 🏗️ Architecture

The system is a simple client-server application.

**Backend:**
The backend is implemented in Python using the FastAPI framework for high performance.
It integrates with OpenAI GPT-5 for natural language understanding and generation.
Medication data (Acamol, Advil, Augmentin, Lipitor, and Benadryl), users and prescriptions, is stored in a SQLite database.

**Frontend:**
A lightweight chat interface built with HTML5, CSS3, and vanilla JavaScript.
Server-Sent Events (SSE) are used to stream responses from the backend in real time.

**Infrastructure:**
Docker and Docker Compose are used to simplify running the application locally. They allow running the backend and frontend with a single command.

## Project Structure

```
pharmacy-agent/
├── backend/            # FastAPI backend, agent logic, and tools
├── frontend/           # Simple chat UI (HTML, CSS, JavaScript)
├── database/           # SQLite database and initialization script
├── Dockerfile
├── docker-compose.yml
├── MULTI_STEP_FLOWS.md # Multi-step workflow demonstrations
├── EVALUATION.md       # Agent evaluation plan
├── evidence/           # Screenshots of example conversations
└── README.md
```

## 🛠️ Tools (Agent Functions)

The agent uses a small set of tools to interact
with the pharmacy database:

- **get_medication_by_name**  
  Retrieves detailed information about a specific
  medication.

- **check_medication_stock**  
  Checks whether a medication is currently
  available in stock.

- **search_medications**  
  Searches medications by category, active
  ingredient, or returns all available medications.

- **check_prescription**  
  Verifies whether a medication requires a
  prescription and whether the user has an active
  one.


## 🚀 Installation and Setup

### How to Run (Docker)

1. Clone the repository and move into the project directory:
   git clone https://github.com/dolevbargig/pharmacy-agent.git
   cd pharmacy-agent

2. Make sure Docker is installed and running on your machine.

3. Create a .env file in the project root and set your OpenAI API key:
   OPENAI_API_KEY=YOUR_KEY_HERE

4. Build and start the application using Docker Compose:
   docker compose up --build

5. Open the application in your browser:
   Frontend (Chat UI): http://localhost:3000
   Backend API: http://localhost:8000
   Health check endpoint: http://localhost:8000/health

6. To stop the application, press Ctrl+C.
   


Enjoy exploring the agent.
