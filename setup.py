#!/usr/bin/env python3
"""
Automates the Dev_Agent README: gVisor-enabled kind cluster + harness + backend.

Run it from the root of the Dev_Agent repo (the folder containing kind_config.yaml):

    python setup_dev_agent.py                 # full setup + port-forward
    python setup_dev_agent.py --install-traefik   # also install Traefik via Helm
    python setup_dev_agent.py --skip-decider      # don't start strands-decider
    python setup_dev_agent.py --no-port-forward
    python setup_dev_agent.py --skip-build    # reuse images you already built

Requirements on the machine running this: Python 3.8+, Docker (running), and either kind + kubectl on PATH, or devbox with kind + kubectl in its devbox.json.
For --install-traefik you also need helm (or `devbox add kubernetes-helm`).
The decision model step (decision_model/) needs uv (or `devbox add uv`).
"""
import argparse
import atexit
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

NODE_IMAGE = "kind-node-gvisor:latest"
DECIDER_DIR = "decision_model"
DECIDER_MODEL = "StrandsAgents/strands-decider-2B-hobson-v19"

BACKEND_IMAGE = "dev-agent:latest"
HARNESS_IMAGE = "dev-agent-harness:latest"

RUNSC_TOML = '[runsc_config]\n  platform = "systrap"\n  network = "host"\n'

# Order matters: runtime class, volume, redis, backend, then harness.
MANIFESTS = [
    "runtime.yaml",
    "pvc.yaml",
    "redis-deployment.yaml",
    "redis-service.yaml",
    "server-deployment.yaml",
    "service.yaml",
    "harness-deployment.yaml",
    "dev-agent-harness-service.yaml",
    "ingress.yaml",  # routes traefik -> harness; needs Traefik (see --install-traefik)
]


# --------------------------------------------------------------------------- helpers
def step(msg):
    print(f"\n==> {msg}", flush=True)


def ok(msg):
    print(f"    [ok] {msg}", flush=True)


def warn(msg):
    print(f"    [warn] {msg}", flush=True)


def die(msg):
    print(f"\n[error] {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def run(cmd, cwd=None, input_text=None, check=True):
    """Run a command, streaming its output. Returns the exit code."""
    print(f"    $ {' '.join(cmd)}", flush=True)
    try:
        rc = subprocess.run(cmd, cwd=cwd, input=input_text, text=True).returncode
    except FileNotFoundError:
        die(f"Command not found: {cmd[0]}")
    if check and rc != 0:
        die(f"Command failed (exit {rc}): {' '.join(cmd)}")
    return rc


def capture(cmd, cwd=None, timeout=60):
    """Run a command quietly. Returns (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "", f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    return r.returncode, r.stdout, r.stderr


# --------------------------------------------------------------------------- decider process state
_decider = {"proc": None, "keep": False}


def stop_decider():
    proc = _decider["proc"]
    if proc is None or proc.poll() is not None:
        return
    print("\nStopping strands-decider...", flush=True)
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        else:
            os.killpg(proc.pid, signal.SIGTERM)  # started in its own session/process group
        proc.wait(timeout=15)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# Runs on normal exit, die(), and Ctrl+C, unless we deliberately leave the server running.
atexit.register(lambda: None if _decider["keep"] else stop_decider())


# --------------------------------------------------------------------------- tool checks
def resolve_tool_prefix(force_devbox):
    """
    Decide how to invoke kind/kubectl.
    - If both are on PATH (and --devbox not forced): call them directly.
    - Otherwise, if devbox is installed: wrap calls in `devbox run --`,
      which is the portable equivalent of activating the devbox environment.
    """
    have_kind = shutil.which("kind") is not None
    have_kubectl = shutil.which("kubectl") is not None
    have_devbox = shutil.which("devbox") is not None

    if have_kind and have_kubectl and not force_devbox:
        ok("kind and kubectl found on PATH")
        return []

    if have_devbox:
        prefix = ["devbox", "run", "--"]
        rc_k, _, _ = capture(prefix + ["kind", "version"], timeout=600)
        rc_c, _, _ = capture(prefix + ["kubectl", "version", "--client"], timeout=600)
        if rc_k == 0 and rc_c == 0:
            ok("devbox found; kind and kubectl are available inside the devbox environment")
            return prefix
        missing = [n for n, rc in (("kind", rc_k), ("kubectl", rc_c)) if rc != 0]
        die(
            f"devbox is installed but {', '.join(missing)} is not in it. "
            "Run `devbox add kind kubectl` in this folder and try again."
        )

    missing = [n for n, h in (("kind", have_kind), ("kubectl", have_kubectl)) if not h]
    die(
        f"Missing required tool(s): {', '.join(missing)}. Install them, or install devbox "
        "(https://www.jetify.com/devbox) and run `devbox add kind kubectl`."
    )


def resolve_uv(prefix):
    """uv from PATH, or from devbox if that's where kind/kubectl came from."""
    if shutil.which("uv"):
        ok("uv found on PATH")
        return ["uv"]
    if prefix:
        rc, _, _ = capture(prefix + ["uv", "--version"], timeout=600)
        if rc == 0:
            ok("uv available inside devbox")
            return prefix + ["uv"]
    die("uv is required for decision_model/. Install it (https://docs.astral.sh/uv/) or run `devbox add uv`.")


def resolve_helm(prefix):
    """Only needed for --install-traefik. Uses devbox if kind/kubectl came from devbox."""
    if prefix:
        rc, _, _ = capture(prefix + ["helm", "version"], timeout=600)
        if rc == 0:
            ok("helm available inside devbox")
            return prefix + ["helm"]
    if shutil.which("helm"):
        ok("helm found on PATH")
        return ["helm"]
    die("--install-traefik needs helm. Install it, or run `devbox add kubernetes-helm`.")


def check_docker():
    if shutil.which("docker") is None:
        die("Docker is not installed or not on PATH.")
    rc, _, err = capture(["docker", "info"], timeout=30)
    if rc != 0:
        die(f"Docker is installed but the daemon isn't reachable. Start Docker.\n{err.strip()}")
    ok("Docker is running")


# --------------------------------------------------------------------------- repo + config checks
def prepare_repo(args):
    repo = Path(args.repo_dir).resolve()
    if not (repo / "kind_config.yaml").exists():
        die(
            f"{repo} doesn't look like the Dev_Agent repo (kind_config.yaml not found). "
            "Run from the repo root or pass --repo-dir."
        )
    return repo


def check_env_file(repo):
    env = repo / "harness" / ".env"
    if not env.exists():
        die(
            f"{env} is missing. Create it with:\n"
            '  GOOGLE_API_KEY=""\n  URI=""\n  DB_NAME="dev-agent"\n  COLLECTION_NAME="agents"'
        )
    values = {}
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    empty = [k for k in ("GOOGLE_API_KEY", "URI") if not values.get(k)]
    if empty:
        warn(
            f"{', '.join(empty)} empty in harness/.env. The harness needs them "
            "(you can also set them later in the dashboard Settings)."
        )
    else:
        ok("harness/.env has GOOGLE_API_KEY and URI")


def check_manifests(repo):
    missing = [m for m in MANIFESTS if not (repo / m).exists()]
    if missing:
        die(f"Missing manifest file(s) in {repo}: {', '.join(missing)}")

    server = (repo / "server-deployment.yaml").read_text()
    harness = (repo / "harness-deployment.yaml").read_text()
    if BACKEND_IMAGE not in server:
        warn(f"server-deployment.yaml doesn't reference `{BACKEND_IMAGE}` (ImagePullBackOff risk)")
    if HARNESS_IMAGE not in harness:
        warn(f"harness-deployment.yaml doesn't reference `{HARNESS_IMAGE}` (ImagePullBackOff risk)")
    if "runtimeClassName: gvisor" not in server:
        warn("server-deployment.yaml has no `runtimeClassName: gvisor`; backend would run unsandboxed")
    ok("manifests present")


# --------------------------------------------------------------------------- README steps
def check_decider_dir(repo):
    d = repo / DECIDER_DIR
    if not d.is_dir():
        die(f"{d} not found. Use --skip-decider if you don't want the decision model step.")
    ok(f"{DECIDER_DIR}/ found")


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def start_decider(repo, uv, model, port, timeout):
    """cd decision_model && uv sync && uv run strands-decider serve <model> --port <port>  (in background)"""
    step(f"Starting strands-decider from {DECIDER_DIR}/")
    if port_open(port):
        warn(f"Port {port} is already in use; assuming strands-decider is already running. Skipping.")
        return
    workdir = repo / DECIDER_DIR
    run(uv + ["sync"], cwd=workdir)

    # `uv run` executes the command inside the venv that `uv sync` just created.
    cmd = uv + ["run", "strands-decider", "serve", model, "--port", str(port)]
    log_path = repo / "strands-decider.log"
    print(f"    $ {' '.join(cmd)}   (logs: {log_path})", flush=True)
    log = open(log_path, "w")
    if os.name == "nt":
        extra = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        extra = {"start_new_session": True}
    proc = subprocess.Popen(cmd, cwd=workdir, stdout=log, stderr=subprocess.STDOUT, **extra)
    _decider["proc"] = proc

    print(f"    Waiting for it to listen on port {port} (first run may download the model)...", flush=True)
    deadline = time.time() + timeout
    last_note = time.time()
    while time.time() < deadline:
        if proc.poll() is not None:
            tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-20:])
            die(f"strands-decider exited early (code {proc.returncode}). Last log lines:\n{tail}")
        if port_open(port):
            ok(f"strands-decider is serving on http://localhost:{port}")
            return
        if time.time() - last_note > 20:
            print("    ...still starting", flush=True)
            last_note = time.time()
        time.sleep(2)
    warn(f"Not listening on port {port} after {timeout}s; continuing. Check {log_path}.")


def docker_build(repo, subdir, dockerfile, tag):
    """Equivalent of: cd <subdir> && docker build -t <tag> -f <dockerfile> . && cd .."""
    context = repo / subdir
    print(f"  [{subdir}/] docker build -f {dockerfile} -t {tag}")
    run(["docker", "build", "-t", tag, "-f", dockerfile, "."], cwd=context)


def check_dockerfiles(repo):
    required = [
        ("backend", "Dockerfile.gvisor-node"),
        ("backend", "Dockerfile.grpc"),
        ("harness", "Dockerfile.harness"),
    ]
    missing = [f"{d}/{f}" for d, f in required if not (repo / d / f).is_file()]
    if missing:
        die(f"Missing Dockerfile(s): {', '.join(missing)}")
    ok("backend/ and harness/ Dockerfiles found")


def build_node_image(repo):
    step("Step 3: build the gVisor-enabled kind node image")
    docker_build(repo, "backend", "Dockerfile.gvisor-node", NODE_IMAGE)


def create_cluster(repo, kind, cluster):
    step("Step 4: create the kind cluster")
    rc, out, _ = capture(kind + ["get", "clusters"])
    if rc == 0 and cluster in out.split():
        ok(f"cluster '{cluster}' already exists; reusing it")
        return
    run(kind + ["create", "cluster", "--name", cluster, "--config", "kind_config.yaml"], cwd=repo)


def configure_runsc(kind, kubectl, cluster):
    step("Configuring runsc.toml on every node (required)")
    rc, out, err = capture(kind + ["get", "nodes", "--name", cluster])
    nodes = [n for n in out.split() if n]
    if rc != 0 or not nodes:
        die(f"Could not list nodes for cluster '{cluster}': {err.strip()}")

    for node in nodes:
        print(f"  node: {node}")
        rc, current, _ = capture(["docker", "exec", node, "cat", "/etc/containerd/runsc.toml"])
        if rc == 0 and current.strip() == RUNSC_TOML.strip():
            ok("runsc.toml already up to date")
            continue
        # Stdin avoids all shell quoting problems (and works the same on Windows).
        run(
            ["docker", "exec", "-i", node, "bash", "-c", "cat > /etc/containerd/runsc.toml"],
            input_text=RUNSC_TOML,
        )
        run(["docker", "exec", node, "systemctl", "restart", "containerd"])
        ok("runsc.toml written and containerd restarted")

    step("Waiting for nodes to be Ready")
    run(kubectl + ["wait", "--for=condition=Ready", "node", "--all", "--timeout=180s"])


def build_and_load_images(repo, kind, cluster):
    step("Step 5: build and load the images")
    docker_build(repo, "backend", "Dockerfile.grpc", BACKEND_IMAGE)
    docker_build(repo, "harness", "Dockerfile.harness", HARNESS_IMAGE)
    run(kind + ["load", "docker-image", BACKEND_IMAGE, "--name", cluster])
    run(kind + ["load", "docker-image", HARNESS_IMAGE, "--name", cluster])


def apply_manifests(repo, kubectl):
    step("Step 6: apply the manifests (in README order)")
    for m in MANIFESTS:
        run(kubectl + ["apply", "-f", m], cwd=repo)

    step("Waiting for deployments to become Available")
    rc = run(
        kubectl + ["wait", "--for=condition=Available", "deployment", "--all", "--timeout=300s"],
        check=False,
    )
    if rc != 0:
        warn("Not every deployment became Available in time. Current state:")
        run(kubectl + ["get", "pods", "-o", "wide"], check=False)
        print("    Debug with: kubectl describe pod <pod>  /  kubectl logs <pod>")
    else:
        ok("all deployments Available")
    run(kubectl + ["get", "pods", "-o", "wide"], check=False)


def verify_sandbox(kubectl):
    step("Step 7: verify the gVisor sandbox")
    rc, out, err = capture(kubectl + ["get", "pods", "-o", "json"])
    if rc != 0:
        warn(f"Could not list pods: {err.strip()}")
        return
    backend = None
    for pod in json.loads(out).get("items", []):
        if pod["spec"].get("runtimeClassName") == "gvisor" and pod["status"].get("phase") == "Running":
            backend = pod["metadata"]["name"]
            break
    if not backend:
        warn("No Running pod with runtimeClassName=gvisor found; skipping dmesg check")
        return
    rc, out, err = capture(kubectl + ["exec", backend, "--", "dmesg"])
    first = out.strip().splitlines()[0] if out.strip() else ""
    if rc != 0 or not first:
        warn(f"dmesg failed in {backend}: {err.strip() or 'no output'}")
        return
    print(f"    {backend}: {first}")
    if "gvisor" in out.lower() or "starting gvisor" in out.lower():
        ok("gVisor banner detected; backend is sandboxed")
    else:
        warn("First dmesg line doesn't look like gVisor. Check runtimeClassName and runsc.toml.")


def find_harness_service(kubectl):
    """Return (name, port) of the harness Service in the default namespace, or None."""
    rc, out, _ = capture(kubectl + ["get", "svc", "-o", "json"])
    if rc != 0:
        return None
    for item in json.loads(out).get("items", []):
        if "harness" in item["metadata"]["name"] and item["spec"].get("ports"):
            return item["metadata"]["name"], item["spec"]["ports"][0]["port"]
    return None


def install_traefik(kubectl, helm, context, chart_version):
    step("Installing Traefik (Helm) in namespace 'traefik'")
    run(helm + ["repo", "add", "traefik", "https://traefik.github.io/charts", "--force-update"])
    run(helm + ["repo", "update"])
    cmd = helm + [
        "upgrade", "--install", "traefik", "traefik/traefik",
        "--namespace", "traefik", "--create-namespace",
        "--kube-context", context,
        "--wait", "--timeout", "5m",
    ]
    if chart_version:
        cmd += ["--version", chart_version]
    run(cmd)
    ok("Traefik installed")


def port_forward(kubectl, local_port):
    step("Step 8: open the web workspace")
    # README target: traefik service in the traefik namespace.
    rc, _, _ = capture(kubectl + ["get", "svc", "traefik", "-n", "traefik"])
    if rc == 0:
        target = ["-n", "traefik", "svc/traefik", f"{local_port}:80"]
    else:
        # Fallback: forward the harness service from dev-agent-harness-service.yaml directly.
        warn("svc/traefik not found in namespace 'traefik'; falling back to the harness service")
        svc = find_harness_service(kubectl)
        if not svc:
            warn("Couldn't find a harness service to forward. Forward it manually with kubectl port-forward.")
            return
        name, port = svc
        target = [f"svc/{name}", f"{local_port}:{port}"]

    print(f"\n    Open http://localhost:{local_port}   (Ctrl+C to stop the port-forward)\n")
    try:
        subprocess.run(kubectl + ["port-forward"] + target)
    except KeyboardInterrupt:
        print("\nPort-forward stopped.")


# --------------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description="Set up Dev_Agent on a local gVisor-enabled kind cluster.")
    p.add_argument("--repo-dir", default=".", help="Path to the Dev_Agent repo (default: current dir)")
    p.add_argument("--cluster", default="my-cluster", help="kind cluster name (default: my-cluster)")
    p.add_argument("--devbox", action="store_true", help="Force running kind/kubectl through devbox")
    p.add_argument("--install-traefik", action="store_true",
                   help="Install Traefik via Helm (README step 8 expects svc/traefik in namespace traefik)")
    p.add_argument("--traefik-chart-version", default=None, help="Pin the Traefik Helm chart version")
    p.add_argument("--skip-decider", action="store_true", help=f"Don't run uv sync / start strands-decider in {DECIDER_DIR}/")
    p.add_argument("--decider-model", default=DECIDER_MODEL, help=f"Model for strands-decider (default: {DECIDER_MODEL})")
    p.add_argument("--decider-port", type=int, default=8080, help="Port for strands-decider (default: 8080)")
    p.add_argument("--decider-timeout", type=int, default=900, help="Seconds to wait for it to start listening (default: 900)")
    p.add_argument("--skip-build", action="store_true", help="Skip docker builds and image loading")
    p.add_argument("--no-port-forward", action="store_true", help="Don't start the port-forward at the end")
    p.add_argument("--local-port", type=int, default=8000, help="Local port for the dashboard (default: 8000)")
    args = p.parse_args()

    step("Checking prerequisites")
    prefix = resolve_tool_prefix(args.devbox)
    kind = prefix + ["kind"]
    context = f"kind-{args.cluster}"
    kubectl = prefix + ["kubectl", "--context", context]
    helm = resolve_helm(prefix) if args.install_traefik else None
    uv = resolve_uv(prefix) if not args.skip_decider else None
    check_docker()

    repo = prepare_repo(args)
    if not args.skip_decider:
        check_decider_dir(repo)
    check_env_file(repo)
    check_manifests(repo)
    if not args.skip_build:
        check_dockerfiles(repo)

    if not args.skip_decider:
        start_decider(repo, uv, args.decider_model, args.decider_port, args.decider_timeout)

    if not args.skip_build:
        build_node_image(repo)
    create_cluster(repo, kind, args.cluster)
    configure_runsc(kind, kubectl, args.cluster)
    if not args.skip_build:
        build_and_load_images(repo, kind, args.cluster)
    if args.install_traefik:
        install_traefik(kubectl, helm, context, args.traefik_chart_version)
    apply_manifests(repo, kubectl)
    verify_sandbox(kubectl)

    if args.no_port_forward:
        if _decider["proc"] is not None:
            _decider["keep"] = True
            print(f"\nstrands-decider left running (PID {_decider['proc'].pid}, logs: {repo / 'strands-decider.log'}).")
        print(f"\nDone. Forward the dashboard with:\n  kubectl --context {context} port-forward -n traefik svc/traefik {args.local_port}:80")
    else:
        port_forward(kubectl, args.local_port)


if __name__ == "__main__":
    main()