# Dev\_Agent 🤖

A modular AI-powered development framework that orchestrates specialized subagents to plan, build, and ship applications — your way.

***

## What is Dev\_Agent?

Dev\_Agent is a multi-agent development system that lets you spin up field-specific subagents, generate custom skills, and build full applications through two distinct execution modes. Whether you want full automation or hands-on control, Dev\_Agent adapts to your workflow.

***

## Features

### 🧩 Subagent Creation

Create specialized subagents tailored to specific domains of software development — frontend, backend, DevOps, ML, mobile, and more. Each subagent carries deep context for its field and operates independently or as part of a pipeline.

### ⚡ Custom Skill Generation

Generate reusable skills that extend any subagent's capabilities. Skills are modular, composable, and can be shared across agents — build once, use everywhere.

### 🚀 App Generation — Two Modes

#### 📋 Plan Mode

The system analyzes your app requirements and **dynamically selects and orchestrates the right subagents** to complete the build. No manual configuration needed — Dev\_Agent figures out who does what.

```
User prompt → Dev_Agent analyzes → Selects agents → Executes pipeline → App
```

#### 🎯 Individual Subagent Mode

You're in control. **Manually select which subagent** handles the task. Ideal for targeted work, debugging specific layers, or when you know exactly which domain needs attention.

```
User selects agent → Assigns task → Agent executes → Output
```

***

## Getting Started

```
git clone https://github.com/Anish-CodeDev/Dev_Agent.git
cd Dev_Agent
pip install -r requirements.txt
python agent.py
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

***

## Usage

### Create a Subagent

```
# Example: spin up a backend-focused subagent
Enter something: I want you to create an agent which is focused on building flask backends.
```

### Generate a Skill

```
Enter something: I want you to create a skill focused on building backend agents.
```

### Build an App

**Plan Mode** — let Dev\_Agent decide:

```
Enter something: Build a REST API with user auth and a dashboard.
```

**Individual Mode** — you pick the agent:

```
Enter something: Build a login UI with React with the help of react-agent.
```

***

## Architecture

```
In the repo you may some folders in the apps folder like DineDash Backend, OrderFlowProject, etc. These are the apps developed by the agents.
Dev_Agent/
├── apps/          # Apps developed by various agents
├── skills/          # Reusable skill modules
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

## Roadmap

* \[ ] Web UI for agent management

* \[ ] Multi-agent parallel execution

* \[ ] CI/CD integration

***

## Contributing

PRs and issues welcome.
