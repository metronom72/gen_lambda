# Gen Lambda

Gen Lambda is a CLI tool designed to simplify the process of creating, publishing, and managing AWS Lambda functions.

## Features

- Create new AWS Lambda functions with customizable configurations.
- Publish Lambda functions to AWS.
- Remove Lambda functions from AWS.
- Zip Lambda functions for deployment.
- Interactive prompts for configuration selection.

## Requirements

Before using Gen Lambda, ensure you have the following installed and configured:

- **Python 3.11+**
- **Python 3.12+**
- **Python 3.13+**
- **Terraform**
- **Node.js 18**
- **Node.js 20**
- **Node.js 22**
- **AWS CLI** (configured with `aws configure`)

## Installation

You can install Gen Lambda via pip:

```sh
pip install gen_lambda
```

Alternatively, you can install it using Poetry:

```sh
pip install poetry
poetry install
```

## Usage

The CLI is powered by `typer`, providing an intuitive interface for managing Lambda functions.

### Setup Commands

```sh
lambda --help
```

#### Create a New Lambda Function

```sh
lambda --generate
```

This command will guide you through selecting:
- Lambda name
- Project name
- Environment (development, staging, production)
- Runtime (from available templates)
- AWS Region
- IAM Role creation

#### Publish an Existing Lambda Function

```sh
lambda --publish
```

#### Remove a Lambda Function

```sh
lambda --remove
```

#### Zip Lambda Function for Deployment

```sh
lambda --zip
```

## Configuration

### AWS Region Selection

You will be prompted to choose from the following AWS regions:

- us-east-1
- us-east-2
- us-west-1
- us-west-2
- eu-central-1
- eu-west-1
- eu-west-2
- eu-west-3
- ap-southeast-1
- ap-southeast-2
- ap-northeast-1
- ap-northeast-2
- ap-south-1
- sa-east-1

### IAM Role Management

Gen Lambda allows you to create a new IAM Role if necessary.

## Development

To contribute or modify the project, use the following setup:

```sh
git clone https://github.com/your-repo/gen_lambda.git
cd gen_lambda
poetry install
```

Run the CLI locally:

```sh
lambda --generate
```

## License

MIT License. See `LICENSE` for details.

## Author

Mikhail Dorokhovich

