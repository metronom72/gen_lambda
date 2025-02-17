import typer
from InquirerPy import prompt
import os
from src.pub_lambda.create_lambda import create_lambda

app = typer.Typer()


def load_runtimes():
    templates_path = "templates"
    try:
        if not os.path.exists(templates_path):
            raise FileNotFoundError(f"Templates directory '{templates_path}' not found.")

        runtimes = [d for d in os.listdir(templates_path) if os.path.isdir(os.path.join(templates_path, d))]

        if not runtimes:
            raise ValueError("No valid runtimes found in the templates directory.")

        return runtimes
    except Exception as e:
        typer.secho(f"Error loading runtimes: {e}", fg=typer.colors.RED)
        raise typer.Exit()


def ask_lambda_name():
    while True:
        try:
            result = prompt([{"type": "input", "name": "lambda_name", "message": "Enter Lambda name:"}])
            lambda_name = result.get("lambda_name", "").strip()
            if lambda_name:
                typer.secho(f"Lambda Name: {lambda_name}", fg=typer.colors.GREEN)
                return lambda_name
            typer.secho("Lambda name is required. Please enter a valid name.", fg=typer.colors.RED)
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


def ask_project_name():
    while True:
        try:
            result = prompt([{"type": "input", "name": "project_name", "message": "Enter project name:"}])
            project_name = result.get("project_name", "").strip()
            if project_name:
                typer.secho(f"Project Name: {project_name}", fg=typer.colors.GREEN)
                return project_name
            typer.secho("Project name is required. Please enter a valid name.", fg=typer.colors.RED)
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


def ask_environment():
    environments = ["development", "staging", "production"]
    while True:
        try:
            result = prompt([
                {"type": "list", "name": "environment", "message": "Select environment:", "choices": environments}
            ])
            environment = result.get("environment", "").strip()
            if environment:
                typer.secho(f"Selected Environment: {environment}", fg=typer.colors.GREEN)
                return environment
            typer.secho("Environment selection is required.", fg=typer.colors.RED)
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


def ask_runtime():
    runtimes = load_runtimes()
    while True:
        try:
            result = prompt([
                {"type": "list", "name": "runtime", "message": "Select runtime:", "choices": runtimes}
            ])
            runtime = result.get("runtime", "").strip()
            if runtime:
                typer.secho(f"Selected Runtime: {runtime}", fg=typer.colors.GREEN)
                return runtime
            typer.secho("Runtime selection is required.", fg=typer.colors.RED)
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


@app.command()
def setup(target_dir: str = typer.Option(None, help="Directory where the Lambda function should be created")):
    typer.secho("Setting up Lambda function...", fg=typer.colors.BLUE)

    try:
        lambda_name = ask_lambda_name()
        project_name = ask_project_name()
        environment = ask_environment()
        runtime = ask_runtime()

        typer.secho("Lambda Configuration:", fg=typer.colors.CYAN, bold=True)
        typer.secho(f"Lambda Name: {lambda_name}", fg=typer.colors.GREEN)
        typer.secho(f"Project Name: {project_name}", fg=typer.colors.GREEN)
        typer.secho(f"Environment: {environment}", fg=typer.colors.GREEN)
        typer.secho(f"Runtime: {runtime}", fg=typer.colors.GREEN)

        create_lambda(lambda_name, project_name, environment, runtime, target_dir)

    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

