# Dev_Agent 🤖

A modular AI-powered development framework that orchestrates specialized subagents to plan, build, and ship applications, your way. The agent harness and its sandboxed execution backend both run in the same local [kind](https://kind.sigs.k8s.io/) cluster. Everything the agents generate is saved, executed and inspected by a [gVisor](https://gvisor.dev/)-sandboxed Go gRPC backend, so AI-written code never runs directly on your machine.

***

## Table of Contents

- [What is Dev_Agent?](#what-is-dev_agent)
- [Features](#features)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Configure environment variables](#2-configure-environment-variables)
  - [3. Build the gVisor-enabled kind node image](#3-build-the-gvisor-enabled-kind-node-image)
  - [4. Create the kind cluster](#4-create-the-kind-cluster)
  - [5. Build and load the images](#5-build-and-load-the-images)
  - [6. Apply the manifests](#6-apply-the-manifests)
  - [7. Verify the sandbox](#7-verify-the-sandbox)
  - [8. Open the web workspace](#8-open-the-web-workspace)
- [Configuring `runsc.toml`](#configuring-runsctoml)
- [gRPC API](#grpc-api)
- [Usage](#usage)
- [Modes at a Glance](#modes-at-a-glance)
- [Common Pitfalls](#common-pitfalls)
- [Security Notes](#security-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

***

## What is Dev_Agent?

Dev_Agent is a multi-agent development system that lets you spin up field-specific subagents, dynamically create custom skills, and build full applications through two distinct execution modes. Whether you want full automation or hands-on control, Dev_Agent adapts to your workflow.

It is made up of two components that are deployed together in one Kubernetes cluster:

| Component | Location | Role |
| --- | --- | --- |
| **Agent harness + dashboard** | `harness/` | Subagents, skills, app builder and web workspace |
| **Sandboxed backend** | `backend/` | Go gRPC server that saves files, runs commands and serves file contents, running under gVisor |

A Redis instance is also deployed in the same cluster alongside them. The repository root contains only the Kubernetes/kind configuration files.

***

## Features

### 🧩 Subagent Creation

Create specialized subagents tailored to specific domains of software development: frontend, backend, DevOps, ML, mobile, and more. Each subagent carries deep context for its field and operates independently or as part of a pipeline.

### ⚡ Custom Skill Generation

The agent **dynamically creates skills** on its own when a task calls for something it doesn't already know how to do, and you can also ask for one explicitly. Skills are saved as reusable modules that extend any subagent's capabilities. They are modular, composable, and can be shared across agents: build once, use everywhere.

### 🚀 App Generation: Two Modes

#### 📋 Plan Mode

The system analyzes your app requirements and **dynamically selects and orchestrates the right subagents** to complete the build. No manual configuration needed; Dev_Agent figures out who does what.

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

### 🖥️ Web Workspace

A dashboard to submit build tasks, browse generated projects, view directory trees and file previews, and chat about a project's implementation.

- Choose **Plan** to use the multi-agent planning flow, or **Individual** to use the conversational agent flow (optionally preferring a specific agent).
- When an agent proposes edits to an existing file, review the current and proposed code in the dashboard and approve or decline the change before it is saved.
- Open a project to view its directory tree and file previews (including remote previews served through the backend's `ViewFile`).
- Use the project-scoped chat to discuss a project's implementation. Chat history is kept for the current browser tab, and **chat does not directly edit files**; submit a task from the App builder to request code changes.
- The project explorer derives each app's directory tree from its `files` paths in `harness/data/context.json`; nested paths such as `src/app.py` appear under their directories.
- The dashboard uses agent records stored in MongoDB Atlas, app context, the Gemini workflow, and the gRPC file service.

***

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  kind cluster (gVisor-enabled nodes)                                    │
│                                                                         │
│  ┌──────────────────────┐   gRPC    ┌─────────────────────────────────┐ │
│  │  Dev_Agent harness   │ ────────► │ Pod (runtimeClassName: gvisor)  │ │
│  │  + web dashboard     │           │  Go gRPC server                 │ │
│  │                      │ ◄──────── │  └─ workspace ◄── PVC mount     │ │
│  └──────────┬───────────┘  results  └─────────────────────────────────┘ │
│             │                                                           │
│  ┌──────────▼───────────┐                                               │
│  │  Redis               │                                               │
│  └──────────────────────┘                                               │
└─────────────▲───────────────────────────────────────────────────────────┘
              │ port-forward (8000)
          Your browser
```

The harness reaches the backend over the cluster's internal network, so the gRPC port does not need to be exposed to your machine.

1. A subagent generates a file and calls `CreateFiles`.
2. The backend saves it to the workspace volume.
3. The agent calls `ExecuteCommands` to install dependencies, run tests, and so on.
4. The agent calls `ViewFile` to read any individual file it wants to inspect.

### Why the setup differs from a normal cluster

kind nodes are Docker containers with containerd running inside them. gVisor (`runsc`) must be installed *inside* the node container, and containerd needs a runtime handler registered for it. There is no separate VM boundary, so you are nesting sandboxing inside kind's own container.

Only the backend pod runs under the `gvisor` runtime class, since it is the one that handles untrusted, AI-generated code.

***

## Repository Layout

```
Dev_Agent/
├── harness/                       # Agent harness + dashboard
│   ├── skills/                    # Reusable skill modules
│   ├── data/
│   │   └── context.json           # App context; file paths drive the project explorer
│   ├── .env                       # Environment variables (never commit)
│   └── Dockerfile.harness         # Harness image
├── backend/                       # Go gRPC server + Dockerfiles
│   ├── (gRPC handler and service functions: CreateFiles, ExecuteCommands, ViewFile)
│   ├── Dockerfile.gvisor-node     # kind node image with gVisor (runsc) installed
│   └── Dockerfile.grpc            # gRPC server image
├── kind_config.yaml               # kind cluster using the gVisor-enabled node image
├── runtime.yaml                   # RuntimeClass mapping `gvisor` to the `runsc` handler
├── pvc.yaml                       # PersistentVolumeClaim for the workspace volume
├── redis-deployment.yaml          # Redis Deployment
├── redis-service.yaml             # Redis Service
├── server-deployment.yaml         # gRPC backend Deployment with runtimeClassName: gvisor
├── service.yaml                   # gRPC backend Service
├── harness-deployment.yaml        # Harness + dashboard Deployment
└── dev-agent-harness-service.yaml # Harness + dashboard Service
```

***

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Go (to build the server)
- A Google API key (for Gemini model access)
- A [MongoDB Atlas](https://www.mongodb.com/atlas) cluster (its connection string goes in your `.env`)

***

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Anish-CodeDev/Dev_Agent.git
cd Dev_Agent
```



### 2. Build the gVisor-enabled kind node image

`backend/Dockerfile.gvisor-node` builds a node image on top of `kindest/node` with gVisor (`runsc`) installed:

```bash
cd backend
docker build -t kind-node-gvisor:latest -f Dockerfile.gvisor-node .
cd ..
```

> Pin the `kindest/node` tag to match your kind CLI version. Mismatches cause hard-to-debug cluster bring-up failures.

### 3. Create the kind cluster

`kind_config.yaml` points the nodes at the `kind-node-gvisor:latest` image and patches containerd at cluster-creation time to register the `runsc` runtime, so nothing needs hand-editing after boot.

```bash
kind create cluster --name my-cluster --config kind_config.yaml
```

Once the cluster is up, complete [Configuring `runsc.toml`](#configuring-runsctoml) before continuing. **It is required.**

### 5. Build and load the images

Build the backend and the harness, then load both into the cluster:

```bash
# gRPC backend
cd backend
docker build -t dev-agent:latest -f Dockerfile.grpc .
cd ..

# Agent harness + dashboard
cd harness
docker build -t dev-agent-harness:latest -f Dockerfile.harness .
cd ..

kind load docker-image dev-agent:latest --name my-cluster
kind load docker-image dev-agent-harness:latest --name my-cluster
```

> For each image, the tag you build, the tag you load, and the `image:` in its manifest must all match, otherwise the pod will end up in `ImagePullBackOff`.

### 6. Apply the manifests

Apply them in this order, so the runtime class, volume, Redis and backend are ready before the harness starts:

```bash
kubectl apply -f runtime.yaml                  # RuntimeClass: gvisor -> runsc
kubectl apply -f pvc.yaml                      # workspace volume
kubectl apply -f redis-deployment.yaml         # Redis
kubectl apply -f redis-service.yaml
kubectl apply -f server-deployment.yaml        # gRPC backend (runtimeClassName: gvisor)
kubectl apply -f service.yaml                  # gRPC backend Service
kubectl apply -f harness-deployment.yaml       # harness + dashboard
kubectl apply -f dev-agent-harness-service.yaml
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik-helm-chart/master/traefik/crds/ingressroute.yaml
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik -n traefik --create-namespace
kubectl apply -f ingress.yaml
```

> Don't use `kubectl apply -f .` here: the repo root also contains `kind_config.yaml`, which is a kind config rather than a Kubernetes resource.

Check that all pods come up:

```bash
kubectl get pods -o wide
```

### 7. Verify the sandbox

```bash
kubectl exec -it <backend-pod> -- dmesg | head -1
# Should show a gVisor-specific fake kernel banner, not your real host kernel
```

### 8. Open the web workspace

Forward the dashboard port to your machine and leave it running:

```bash
kubectl port-forward -n traefik svc/traefik 8000:80
```

Open `http://localhost:8000` to submit a build task and browse generated projects.



***

## Configuring `runsc.toml`

**This step is required.** The containerd patch in `kind_config.yaml` points the `runsc` runtime at `/etc/containerd/runsc.toml`, so the file must exist on every node before you deploy anything. Run these steps after creating the cluster (and any time you change the config), repeating for each node. `systrap` is generally the fastest platform for trapping syscalls (faster than `ptrace`); fall back to `ptrace` only if you hit compatibility issues.

1. Identify the node containers (with `my-cluster` they are `my-cluster-control-plane` and `my-cluster-worker`). If a pod is already running, you can see which node it landed on in the `NODE` column:

   ```bash
   kubectl get nodes
   kubectl get pod <pod-name> -o wide
   ```

2. Check whether the config file already exists on that node:

   ```bash
   docker exec -it <NODE> cat /etc/containerd/runsc.toml
   ```

3. If it's missing or out of date, write it and restart containerd:

   ```bash
   docker exec -it <NODE> bash -c 'cat <<EOF > /etc/containerd/runsc.toml
   [runsc_config]
     platform = "systrap"
     network = "host"
   EOF'
   docker exec -it <NODE> systemctl restart containerd
   ```

***

## gRPC API

| RPC | Description |
| --- | --- |
| `CreateFiles` | Saves one or more generated files to the workspace volume |
| `ExecuteCommands` | Runs commands inside the sandboxed pod |
| `ViewFile` | Returns the contents of an individual file, chosen by the agent |

***

## Usage

Enter prompts like these in the web dashboard.

### Create a Subagent

Agents be created from the agents tab in the live dashboard

### Generate a Skill

Skills can be created from the skills tab in the live dashboard; skills are also dynamically created by the agent during runtime.

### Build an App

**Plan Mode**: let Dev_Agent decide:

```
Build a REST API with user auth and a dashboard.
```

**Individual Mode**: you pick the agent:

```
Build a login UI with React with the help of react-agent.
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

## Common Pitfalls

- **Unpinned node image:** forgetting to match the `kindest/node` tag to your kind CLI version breaks cluster bring-up.
- **Missing `runsc.toml`:** the file must exist on every node before deploying; otherwise the `runsc` runtime won't start.
- **Mismatched image tags:** the tag you build, the tag you load into kind, and the `image:` in each manifest must all match, or the pod ends up in `ImagePullBackOff`.
- **Missing `runtimeClassName`:** applying the RuntimeClass but not setting `runtimeClassName` on the backend pod spec means the pod silently runs unsandboxed.
- **Redis not running:** the harness depends on Redis; if it fails to start or connect, check that the Redis pod and Service are up.
- **Harness can't reach the backend:** if file creation, command execution or previews fail in the dashboard, check that the backend pod is running and that the harness is pointed at the backend's in-cluster Service address on port `9000`.
- **No latency testing:** netstack overhead is the thing most likely to surprise you. Load-test gRPC latency before and after enabling gVisor.

***

## Security Notes

- gVisor significantly reduces host attack surface but isn't a silver bullet. Keep the cluster local and treat it as a development tool.
- The server resolves incoming file paths against the workspace root and should reject anything that escapes it (`../`, absolute paths, symlinks).
- Keep the backend's gRPC Service cluster-internal (`ClusterIP`). If you expose it beyond the cluster, add TLS and authentication.
- Only the dashboard port is forwarded to your machine; keep that on localhost too.
- Never commit your `.env` file.

***

## Roadmap

* [ ] Web UI for agent management

* [ ] Multi-agent parallel execution

* [ ] CI/CD integration

* [ ] Autonomous debugging

***

## Contributing

PRs and issues welcome.