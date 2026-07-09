import os
import shutil
import subprocess


NPM = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"


def run(command, env=None):
    subprocess.run(command, env=env, check=True)


def main():
    frontend_env = os.environ.copy()
    frontend_env.setdefault("VITE_BASE_PATH", "/static/")

    if not os.getenv("VERCEL") and not os.path.exists("node_modules"):
        run([NPM, "ci"])

    run([NPM, "run", "build"], env=frontend_env)


if __name__ == "__main__":
    main()
