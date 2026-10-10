# Dev_Agent 🤖

A modular AI-powered development framework that orchestrates specialized subagents to plan, build, and ship applications — your way. Generated code is saved, executed and inspected inside a gVisor-sandboxed gRPC backend, so AI-written code never runs directly on your machine.

***

## What is Dev_Agent?

Dev_Agent is a multi-agent development system that lets you spin up field-specific subagents, dynamically create custom skills, and build full applications through two distinct execution modes. Whether you want full automation or hands-on control, Dev_Agent adapts to your workflow.

Dev_Agent is made up of two parts:

| Part | Repo | Role |
| --- | --- | --- |
| **Agent + dashboard** (this repo) | [Dev_Agent](https://github.com/Anish-CodeDev/Dev_Agent) | Python agents and web workspace |
| **Sandboxed backend** | [Dev_Agent_Backend](https://github.com/Anish-CodeDev/Dev_Agent_Backend) | Go gRPC server that saves files, runs commands and serves file contents, under gVisor on a kind cluster |

***

## Features

### 🧩 Subagent Creation

Create specialized subagents tailored to specific domains of software development — frontend, backend, DevOps, ML, mobile, and more. Each subagent carries deep context for its field and operates independently or as part of a pipeline.

### ⚡ Custom Skill Generation

The agent **dynamically creates skills** on its own when a task calls for something it doesn't already know how to do, and you can also ask for one explicitly. Skills are saved as reusable modules that extend any subagent's capabilities. They are modular, composable, and can be shared across agents — build once, use everywhere.

### 🚀 App Generation — Two Modes

#### 📋 Plan Mode

The system analyzes your app requirements and **dynamically selects and orchestrates the right subagents** to complete the build. No manual configuration needed — Dev_Agent figures out who does what.

```
User prompt → Dev_Agent analyzes → Selects agents → Executes pipeline → App
```

#### 🎯 Individual Subagent Mode

You're in control. **Manually select which subagent** handles the task. Ideal for targeted work, debugging specific layers, or when you know exactly which domain needs attention.

```
User selects agent → Assigns task → Agent executes → Output
```

### 🛡️ Sandboxed Execution Backend

Everything the agents generate goes through a dedicated gRPC backend instead of touching your host:

- 📁 **File creation** (`CreateFiles`): generated files are sent to the backend and saved to a persistent volume mount, so projects survive pod restarts.
- ⚙️ **Command execution** (`ExecuteCommands`): installs, builds and tests run inside the sandboxed pod, not on your machine.
- 👀 **File viewing** (`ViewFile`): the agent can read back any individual file it chooses, which lets it review and refine its own output.
- 🔒 **gVisor isolation**: the backend pod runs under the `runsc` runtime, placing a user-space kernel between untrusted code and the host.
- ☸️ **Kind-based deployment**: a reproducible, local Kubernetes setup.

```
Dev_Agent ──gRPC (localhost:9000)──► kind cluster ──► gVisor pod (Go gRPC server) ──► workspace volume
```

### 🖥️ Web Workspace

A dashboard to submit build tasks, browse generated projects, view directory trees and file previews, and chat about a project's implementation. See [Web workspace](#web-workspace) below.

***

## Getting Started

```bash
# Clone Dev_Agent
git clone https://github.com/Anish-CodeDev/Dev_Agent.git
cd Dev_Agent
pip install -r requirements.txt

# Clone the backend service
git clone https://github.com/Anish-CodeDev/Dev_Agent_Backend.git
```

### Environment Setup

Create a `.env` file in the root of the project and populate it with the following fields:

```env
GOOGLE_API_KEY=""
URI=""
DB_NAME="dev-agent"
COLLECTION_NAME="agents"
```

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Your Google API key for AI model access |
| `URI` | Connection URI for your database |
| `DB_NAME` | Name of the database (default: `dev-agent`) |
| `COLLECTION_NAME` | Collection where agents are stored (default: `agents`) |

> Never commit your `.env` file. Make sure it's listed in `.gitignore`.

### Backend Setup

The agent needs the backend running to create files, execute commands and view files. In short:

1. Build the gVisor-enabled kind node image (`kind-node-gvisor:latest`).
2. Create the kind cluster (`my-cluster`) from `kind_config.yaml`.
3. Write the required `runsc.toml` to every node and restart containerd.
4. Build the gRPC server image and load it into the cluster.
5. Apply `runtime.yaml`, `pvc.yaml` and `server-deployment.yaml`.

Once the pod is running, the gRPC server is available at `localhost:9000`. If the port isn't already exposed:

```bash
kubectl port-forward deploy/dev-agent-deployment 9000:9000
```

Full step-by-step instructions, `runsc.toml` configuration, debugging and common pitfalls are in the [backend README](https://github.com/Anish-CodeDev/Dev_Agent_Backend#readme).

### Web workspace

Start the file-management gRPC service on port `9000`, then launch the dashboard from the repository root:

```bash
uvicorn server:main
```

Open `http://localhost:8000` to submit a build task and browse generated projects. Open a project to view its directory tree and file previews, and use the project-scoped chat to discuss its implementation. Chat history is kept for the current browser tab, and chat does not directly edit files; submit a task from the App builder to request code changes. The project explorer derives each app's directory tree from its `files` paths in `data/context.json`; nested paths such as `src/app.py` appear under their directories. Choose Plan to use the multi-agent planning flow or Individual to use the conversational agent flow; in Individual mode, you can optionally prefer a specific agent. The FastAPI dashboard uses MongoDB agent records, app context, the Gemini workflow, and the gRPC file service. The gRPC service must be running for file creation, command execution, and remote file previews.

***

## Usage

Enter prompts like these in the web dashboard.

### Create a Subagent

```
# Example: spin up a backend-focused subagent
I want you to create an agent which is focused on building flask backends.
```

### Generate a Skill

```
I want you to create a skill focused on building backend agents.
```

### Build an App

**Plan Mode** — let Dev_Agent decide:

```
Build a REST API with user auth and a dashboard.
```

**Individual Mode** — you pick the agent:

```
Build a login UI with React with the help of react-agent.
```

***

## Architecture

```
┌──────────────────┐        gRPC         ┌───────────────────────────────────────┐
│   Dev_Agent      │ ──────────────────► │  kind cluster (gVisor-enabled nodes)  │
│  Web dashboard   │                     │  ┌─────────────────────────────────┐  │
│                  │ ◄────────────────── │  │ Pod (runtimeClassName: gvisor)  │  │
└──────────────────┘       results       │  │  Go gRPC server                 │  │
                                         │  │  └─ workspace ◄── PVC mount     │  │
                                         │  └─────────────────────────────────┘  │
                                         └───────────────────────────────────────┘
```

1. A subagent generates a file and calls `CreateFiles`.
2. The backend saves it to the workspace volume.
3. The agent calls `ExecuteCommands` to install dependencies, run tests, and so on.
4. The agent calls `ViewFile` to read any individual file it wants to inspect.

Repository layout:

```
Dev_Agent/
├── apps/          # Apps developed by various agents (e.g. DineDash Backend, OrderFlowProject)
├── skills/        # Reusable skill modules
```

***

## Modes at a Glance

| Feature         | Plan Mode       | Individual Mode    |
| --------------- | --------------- | ------------------ |
| Agent selection | Automatic       | Manual             |
| Best for        | Full app builds | Targeted tasks     |
| Control level   | Low (automated) | High (user-driven) |
| Speed           | Fast            | Flexible           |

***

## Security Notes

- gVisor significantly reduces host attack surface but isn't a silver bullet. Keep the cluster local and treat it as a development tool.
- The backend should resolve incoming file paths against the workspace root and reject anything that escapes it (`../`, absolute paths, symlinks).
- If you expose the gRPC port beyond localhost, add TLS and authentication.

***

## Roadmap

* [ ] Web UI for agent management

* [ ] Multi-agent parallel execution

* [ ] CI/CD integration

* [ ] Autonomous debugging

***

## Contributing

PRs and issues welcome.
