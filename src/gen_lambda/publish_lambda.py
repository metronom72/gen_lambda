import json
import re
import shutil
import subprocess
import os
import sys
import typer
from pathlib import Path
from zipfile import ZipFile


def get_runtime_from_tfvars(tfvars_path: Path) -> str:
    if not tfvars_path.exists():
        print("Error: terraform.tfvars not found in infra/ folder.")
        raise typer.Exit()

    with tfvars_path.open() as f:
        content = f.read()

    match = re.search(r'runtime\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    else:
        print("Error: 'runtime' variable not found in terraform.tfvars.")
        raise typer.Exit()


def get_template_from_tfvars(tfvars_path: Path) -> str:
    if not tfvars_path.exists():
        print("Error: terraform.tfvars not found in infra/ folder.")
        raise typer.Exit()

    with tfvars_path.open() as f:
        content = f.read()

    match = re.search(r'lambda_template\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    else:
        print("Error: 'lambda_template' variable not found in terraform.tfvars.")
        raise typer.Exit()


def zip_lambdas():
    cwd = Path.cwd()
    lambda_name = cwd.name
    zip_filename = f"{lambda_name}.zip"
    zip_path = cwd / zip_filename
    dist_dir = cwd / "dist"
    package_json_path = cwd / "package.json"
    tfvars_path = cwd / "infra/terraform.tfvars"

    template = get_template_from_tfvars(tfvars_path)
    runtime = get_runtime_from_tfvars(tfvars_path)

    if zip_path.exists():
        print(f"Removing old ZIP file: {zip_filename}")
        zip_path.unlink()

    if template.startswith("nodejs"):
        if package_json_path.exists():
            with package_json_path.open() as f:
                package_json = json.load(f)
            if "build" in package_json.get("scripts", {}):
                print("Running npm build script...")
                subprocess.run(["npm", "run", "build"], cwd=cwd, check=True)
            else:
                print("No 'build' script found in package.json. Skipping build step.")

        if not dist_dir.exists():
            print("Error: Build process did not produce a 'dist' folder.")
            raise typer.Exit()

        src_lambda_js = dist_dir / "lambda.js"
        target_lambda_js = dist_dir / "lambda_function.js"
        if src_lambda_js.exists():
            shutil.move(src_lambda_js, target_lambda_js)
            print(f"Moved {src_lambda_js} → {target_lambda_js}")
        else:
            print(f"Warning: {src_lambda_js} does not exist. Skipping move.")

        print(f"Creating ZIP: {zip_path}")
        with ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(dist_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(dist_dir)
                    zipf.write(file_path, arcname)

        print(f"ZIP created: {zip_path}")

    elif template.startswith("python"):
        venv_dir = cwd / ".venv"
        if not venv_dir.exists():
            print("Error: .venv not found. Run install_dependencies first.")
            raise typer.Exit()

        print(f"Creating ZIP: {zip_path}")
        with ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(cwd):
                if any(exclude in root for exclude in ["infra", "node_modules", ".venv"]):
                    continue
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(cwd)
                    zipf.write(file_path, arcname)

        print(f"ZIP created: {zip_path}")

    elif template.startswith("go"):
        go_binary = cwd / "dist/bootstrap"
        go_source = cwd / "cmd/handler/main.go"

        print("Building Go Lambda binary for Amazon Linux (ARM64)...")

        env = os.environ.copy()
        env["GOOS"] = "linux"
        env["GOARCH"] = "arm64"
        env["CGO_ENABLED"] = "0"

        build_command = [
            "go", "build",
            "-tags", "lambda.norpc",
            "-trimpath",
            "-ldflags", "-s -w",
            "-o", str(go_binary),
            str(go_source)
        ]

        try:
            subprocess.run(build_command, cwd=cwd, check=True, env=env, capture_output=True, text=True)
            print("Go build completed successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error: Go build failed.\n{e.stderr}")
            raise typer.Exit()

        if not go_binary.exists():
            print("Error: Go build failed, bootstrap binary not found.")
            raise typer.Exit()

        print(f"Creating ZIP: {zip_path}")
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(go_binary, "bootstrap")  # Ensure "bootstrap" is at the root

        print(f"ZIP created: {zip_path}")

    else:
        print(f"Unsupported template: {template}, with runtime: {runtime}. Skipping zipping process.")
        raise typer.Exit()


def publish_lambda():
    infra_dir = "infra"

    if not os.path.isdir(infra_dir):
        print(f"Error: Directory '{infra_dir}' does not exist.")
        sys.exit(1)

    zip_lambdas()

    try:
        os.chdir(infra_dir)

        print("Initializing Terraform...")
        subprocess.run(["terraform", "init"], check=True)

        print("Applying Terraform configuration...")
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        print("Terraform apply completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"Terraform execution failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        os.chdir("..")
