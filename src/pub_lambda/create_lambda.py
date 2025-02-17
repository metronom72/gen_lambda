import shutil
import os
import typer


def create_lambda(lambda_name: str, project_name: str, environment: str, runtime: str, target_dir: str = None):
    templates_dir = "../../templates"
    target_dir = target_dir or os.getcwd()
    lambda_target_dir = os.path.join(target_dir, lambda_name)
    infra_dir = os.path.join(lambda_target_dir, "infra")  # FIX: Ensure infra is inside lambda dir
    tfvars_file = os.path.join(infra_dir, "terraform.tfvars")

    try:
        source_template = os.path.join(templates_dir, runtime)
        if not os.path.exists(source_template):
            typer.secho(f"Error: Runtime template '{runtime}' not found in '{templates_dir}'", fg=typer.colors.RED)
            raise typer.Exit()

        if os.path.exists(lambda_target_dir):
            typer.secho(f"Warning: Target directory '{lambda_target_dir}' already exists. Overwriting.",
                        fg=typer.colors.YELLOW)
            shutil.rmtree(lambda_target_dir)

        shutil.copytree(source_template, lambda_target_dir)
        typer.secho(f"Copied template '{runtime}' to '{lambda_target_dir}'", fg=typer.colors.GREEN)

        variables = {
            "LAMBDA_NAME": lambda_name,
            "PROJECT_NAME": project_name,
            "ENVIRONMENT": environment,
            "RUNTIME": runtime,
            "LAMBDA_PATH": lambda_target_dir
        }

        env_file = os.path.join(lambda_target_dir, ".env")
        with open(env_file, "w") as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")
        typer.secho(f"Created .env file at '{env_file}'", fg=typer.colors.GREEN)

        os.makedirs(infra_dir, exist_ok=True)

        if not os.path.exists(tfvars_file) or os.stat(tfvars_file).st_size == 0:
            with open(tfvars_file, "w") as f:
                f.write("# Terraform Variables\n")

        with open(tfvars_file, "r") as f:
            existing_content = f.read()

        with open(tfvars_file, "a") as f:
            for key, value in variables.items():
                formatted_entry = f'{key.lower()} = "{value}"\n'
                if formatted_entry not in existing_content:
                    f.write(formatted_entry)

        typer.secho(f"Updated Terraform variables file at '{tfvars_file}'", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit()
