import subprocess


def remove_lambda():
    try:
        subprocess.run(["terraform", "destroy", "-auto-approve"], cwd="infra", check=True)
        print("Terraform destroy executed successfully in the 'infra' folder.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Terraform destroy failed with exit code {e.returncode}")
