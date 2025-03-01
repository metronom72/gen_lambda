import re
import shutil
import os
import subprocess

import typer
from pathlib import Path
import importlib.resources as pkg_resources


def extract_runtime(runtime: str) -> str:
    if runtime.startswith("go"):
        match = re.search(r"\(?(provided\.al2|provided\.al2023)\)?", runtime)
        if match:
            return match.group(1)
        typer.secho(f"Error: Invalid Go runtime format '{runtime}'. Expected 'go(provided.al2)' or 'go(provided.al2023)'.", fg=typer.colors.RED)
        raise typer.Exit()
    return runtime


def extract_language(runtime: str) -> str:
    return "go" if runtime.startswith("go") else runtime


def get_templates_dir():
    try:
        typer.secho(pkg_resources)
        templates_path = pkg_resources.files(__package__) / "templates"
    except AttributeError:
        typer.secho(__file__)
        templates_path = Path(__file__).resolve().parent / "templates"

    filtered_parts = [part for part in templates_path.parts if part != "infra"]
    filtered_path = Path(*filtered_parts)

    return str(filtered_path)


def get_infra_dir():
    try:
        templates_path = pkg_resources.files(__package__) / "templates"
    except AttributeError:
        typer.secho(__file__)
        templates_path = Path(__file__).resolve().parent / "templates"

    filtered_parts = [part for part in templates_path.parts if part == "infra"]
    filtered_path = Path(*filtered_parts)

    return str(filtered_path)


def install_dependencies(runtime: str, lambda_target_dir: Path):
    try:
        if runtime.startswith("python"):
            venv_dir = lambda_target_dir / ".venv"
            pip_executable = venv_dir / "bin" / "pip"

            if not venv_dir.exists():
                typer.secho("Creating Python virtual environment...", fg=typer.colors.BLUE)
                subprocess.run(["python", "-m", "venv", str(venv_dir)], cwd=lambda_target_dir, check=True)
                typer.secho("Virtual environment created successfully.", fg=typer.colors.GREEN)

            requirements_file = lambda_target_dir / "requirements.txt"
            if requirements_file.exists():
                typer.secho(
                    f"Installing Python dependencies from '{requirements_file}' inside the virtual environment...",
                    fg=typer.colors.BLUE)

                subprocess.run([str(pip_executable), "install", "-r", str(requirements_file)], cwd=lambda_target_dir,
                               check=True)

                typer.secho("Python dependencies installed successfully.", fg=typer.colors.GREEN)
            else:
                typer.secho("No requirements.txt file found. Skipping Python dependency installation.",
                            fg=typer.colors.YELLOW)

        elif runtime.startswith("nodejs"):
            package_json = lambda_target_dir / "package.json"
            if package_json.exists():
                typer.secho(f"Installing Node.js dependencies in '{lambda_target_dir}'...", fg=typer.colors.BLUE)
                subprocess.run(["npm", "install"], cwd=lambda_target_dir, check=True)
                typer.secho("Node.js dependencies installed successfully.", fg=typer.colors.GREEN)
            else:
                typer.secho("No package.json file found. Skipping Node.js dependency installation.",
                            fg=typer.colors.YELLOW)
        elif runtime.startswith("go"):
            go_mod_file = lambda_target_dir / "go.mod"

            if not go_mod_file.exists():
                typer.secho("go.mod file not found. Initializing Go module...", fg=typer.colors.BLUE)

                module_name = f"{lambda_target_dir.name}"

                subprocess.run(["go", "mod", "init", module_name], cwd=lambda_target_dir, check=True)
                typer.secho(f"Go module '{module_name}' initialized successfully.", fg=typer.colors.GREEN)

            typer.secho(f"Installing Go dependencies in '{lambda_target_dir}'...", fg=typer.colors.BLUE)
            subprocess.run(["go", "mod", "tidy"], cwd=lambda_target_dir, check=True)
            typer.secho("Go dependencies installed successfully.", fg=typer.colors.GREEN)

        else:
            typer.secho(f"Unsupported runtime: {runtime}. Skipping dependency installation.", fg=typer.colors.RED)

    except subprocess.CalledProcessError as e:
        typer.secho(f"Error: Dependency installation failed for runtime '{runtime}'. Exit code: {e.returncode}",
                    fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=e.returncode)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit()


def create_lambda(lambda_name: str, project_name: str, environment: str, runtime: str, aws_region: str, target_dir: str = None, create_role: bool = False):
    templates_dir = Path(get_templates_dir())
    target_dir = Path(target_dir or os.getcwd())
    lambda_target_dir = target_dir / lambda_name
    lambda_build_dir = lambda_target_dir
    archive_path = lambda_build_dir / f"{lambda_name}.zip"

    try:
        source_template = templates_dir / runtime
        if not source_template.exists():
            typer.secho(f"Error: Runtime template '{runtime}' not found in '{templates_dir}'", fg=typer.colors.RED)
            raise typer.Exit()

        if lambda_target_dir.exists():
            typer.secho(f"Warning: Target directory '{lambda_target_dir}' already exists. Overwriting.", fg=typer.colors.YELLOW)
            shutil.rmtree(lambda_target_dir)

        shutil.copytree(source_template, lambda_target_dir)
        typer.secho(f"Copied template '{runtime}' to '{lambda_target_dir}'", fg=typer.colors.GREEN)

        gitignore_template = lambda_target_dir / ".gitignore.template"
        gitignore_target = lambda_target_dir / ".gitignore"

        if gitignore_template.exists():
            gitignore_template.rename(gitignore_target)
            typer.secho(f"Renamed '.gitignore.template' to '.gitignore' in '{lambda_target_dir}'", fg=typer.colors.GREEN)

        templates_infra_dir = templates_dir / "infra"
        target_infra_dir = lambda_target_dir / "infra"

        if templates_infra_dir.exists():
            shutil.copytree(templates_infra_dir, target_infra_dir, dirs_exist_ok=True)
            typer.secho(f"Copied infra folder from global template to '{target_infra_dir}'", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Warning: No global infra folder found in '{templates_dir}'", fg=typer.colors.YELLOW)

        variables = {
            "LAMBDA_NAME": lambda_name,
            "PROJECT_NAME": project_name,
            "ENVIRONMENT": environment,
            "RUNTIME": extract_runtime(runtime),
            "LAMBDA_PATH": str(lambda_target_dir),
            "ARCHIVE_PATH": str(archive_path),
            "AWS_REGION": aws_region,
            "LAMBDA_TEMPLATE": runtime,
        }

        env_file = lambda_target_dir / ".env"
        env_file.write_text("\n".join(f"{key}={value}" for key, value in variables.items()) + "\n")
        typer.secho(f"Created .env file at '{env_file}'", fg=typer.colors.GREEN)

        target_infra_dir.mkdir(parents=True, exist_ok=True)

        tfvars_file = target_infra_dir / "terraform.tfvars"
        if not tfvars_file.exists():
            tfvars_file.write_text("# Terraform Variables\n")
            typer.secho(f"Created missing Terraform variables file at '{tfvars_file}'", fg=typer.colors.GREEN)

        tfvars_content = tfvars_file.read_text()
        new_entries = [f'{key.lower()} = "{value}"\n' for key, value in variables.items() if f'{key.lower()} = "' not in tfvars_content]

        if create_role:
            templates_infra_dir = templates_dir / "infra"
            role_template = templates_infra_dir / "role.tf"
            role_target = target_infra_dir / "role.tf"

            if role_template.exists():
                shutil.copy(role_template, role_target)
                typer.secho(f"Copied IAM role template to '{role_target}'", fg=typer.colors.GREEN)
            else:
                typer.secho("Warning: 'role.tf' template not found, skipping IAM role creation.", fg=typer.colors.YELLOW)

        if new_entries:
            with tfvars_file.open("a") as f:
                f.writelines(new_entries)
            typer.secho(f"Updated Terraform variables file at '{tfvars_file}'", fg=typer.colors.GREEN)

        install_dependencies(extract_language(runtime), lambda_target_dir)

    except Exception as e:
        typer.secho(f"Unexpected error: {str(e)}", fg=typer.colors.RED, bold=True)
        raise typer.Exit()
