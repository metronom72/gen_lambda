import importlib
from pathlib import Path

import typer
from InquirerPy import prompt
from gen_lambda.create_lambda import create_lambda

app = typer.Typer()


def ask_aws_region():
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
        "ap-south-1", "sa-east-1"
    ]
    while True:
        try:
            result = prompt([
                {"type": "list", "name": "aws_region", "message": "Select AWS region:", "choices": regions}
            ])
            aws_region = result.get("aws_region", "").strip()
            if aws_region:
                typer.secho(f"Selected AWS Region: {aws_region}", fg=typer.colors.GREEN)
                return aws_region
            typer.secho("AWS region selection is required.", fg=typer.colors.RED)
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


def ask_create_new_role():
    while True:
        try:
            result = prompt([
                {"type": "confirm", "name": "create_role", "message": "Do you want to create a new AWS IAM Role?"}
            ])
            create_role = result.get("create_role", False)
            typer.secho(f"Create New Role: {'Yes' if create_role else 'No'}", fg=typer.colors.GREEN)
            return create_role
        except KeyboardInterrupt:
            typer.secho("Operation canceled by user.", fg=typer.colors.YELLOW)
            raise typer.Exit()


def load_runtimes():
    try:
        typer.secho("Loading runtimes...", fg=typer.colors.CYAN)

        try:
            package_name = __package__ or "__main__"
            templates_path = importlib.resources.files(package_name) / "templates"
            typer.secho(f"Using importlib.resources for package: {package_name}", fg=typer.colors.BLUE)
        except AttributeError:
            templates_path = Path(__file__).resolve().parent / "templates"
            typer.secho("Fallback to __file__ method", fg=typer.colors.YELLOW)

        typer.secho(f"Resolved templates directory: {templates_path}", fg=typer.colors.GREEN)

        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory '{templates_path}' not found.")

        runtimes = [d.name for d in templates_path.iterdir() if d.is_dir() and d.name != "infra"]

        if not runtimes:
            raise ValueError("No valid runtimes found in the templates directory (excluding 'infra').")

        typer.secho(f"Discovered runtimes (excluding 'infra'): {runtimes}", fg=typer.colors.MAGENTA)
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
    default_project_name = Path.cwd().name
    while True:
        try:
            result = prompt([{
                "type": "input",
                "name": "project_name",
                "message": f"Enter project name (default: {default_project_name}):"
            }])
            project_name = result.get("project_name", "").strip() or default_project_name
            typer.secho(f"Project Name: {project_name}", fg=typer.colors.GREEN)
            return project_name
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
def setup(
        target_dir: str = typer.Option(None, help="Directory where the Lambda function should be created"),
        publish: bool = typer.Option(False, "--publish", help="Publish the Lambda function"),
        remove: bool = typer.Option(False, "--remove", help="Remove the Lambda function"),
        generate: bool = typer.Option(False, "--generate", help="Generate new Lambda function"),
        zip: bool = typer.Option(False, "--zip", help="Zip Lambda function"),
):
    typer.secho("Setting up Lambda function...", fg=typer.colors.BLUE)

    try:
        if not any([publish, remove, generate, zip]):
            typer.secho("Error: You must provide at least one action (--publish, --remove, --zip, or --generate).",
                        fg=typer.colors.RED, bold=True)
            raise typer.Exit(code=1)

        if zip:
            from gen_lambda.publish_lambda import zip_lambdas
            typer.secho("Zip Lambda function...", fg=typer.colors.CYAN, bold=True)
            zip_lambdas()
            return

        if publish:
            from gen_lambda.publish_lambda import publish_lambda
            typer.secho("Publishing Lambda function...", fg=typer.colors.CYAN, bold=True)
            publish_lambda()
            return

        if remove:
            from gen_lambda.remove_lambda import remove_lambda
            typer.secho("Removing Lambda function...", fg=typer.colors.YELLOW, bold=True)
            remove_lambda()
            return

        if generate:
            lambda_name = ask_lambda_name()
            project_name = ask_project_name()
            environment = ask_environment()
            runtime = ask_runtime()
            aws_region = ask_aws_region()
            create_role = ask_create_new_role()

            typer.secho("Lambda Configuration:", fg=typer.colors.CYAN, bold=True)
            typer.secho(f"Lambda Name: {lambda_name}", fg=typer.colors.GREEN)
            typer.secho(f"Project Name: {project_name}", fg=typer.colors.GREEN)
            typer.secho(f"Environment: {environment}", fg=typer.colors.GREEN)
            typer.secho(f"Runtime: {runtime}", fg=typer.colors.GREEN)
            typer.secho(f"AWS Region: {aws_region}", fg=typer.colors.GREEN)
            typer.secho(f"Create New Role: {'Yes' if create_role else 'No'}", fg=typer.colors.GREEN)

            create_lambda(lambda_name, project_name,
                          environment, runtime, aws_region,
                          target_dir, create_role)

            typer.secho("Lambda function generated successfully!", fg=typer.colors.GREEN, bold=True)

    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)
