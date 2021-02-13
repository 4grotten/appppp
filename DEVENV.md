# HOWTO: Set up dev env (DRAFT)
- [Preparing local development environment](#preparing-local-development-environment)
  - [Required programs](#required-programs)
  - [Getting source code](#getting-source-code)
  - [If you want use different Python version](#if-you-want-use-different-python-version)
    - [Installing pyenv](#installing-pyenv)
	- [Installing proper Python version](#installing-proper-python-version)
  - [Install pipenv](#install-pipenv)
  - [Install Pipenv environment](#install-pipenv-environment)
- [Preparing docker development environment](#preparing-docker-development-environment)
  - [Running docker-compose base env](#running-docker-compose-base-environment)
  - [Running all env in docker-compose](#running-all-environment-in-docker-compose)

## Preparing local development environment

### Required programs
- docker
- docker-compose
- git (lol, you are developer)
- curl
- build tools (build-essential)
- zlib
- libpq
- libjpeg
- gdal

### Getting source code
1. Clone this repository
2. Go to local repository directory (with cd, of course)

### If you want use different Python version
Use this instruction only if your system Python version is too old.
If you satisfied with system version, goto [Install pipenv](#Install pipenv)
#### Installing pyenv
1. Install pyenv with automatic installer
```bash
curl https://pyenv.run | bash
```
2. Follow install programm sugestions (add PATH's etc)

If you have problems, see https://github.com/pyenv/pyenv/wiki/Common-build-problems

#### Installing proper Python version
1. Install Python with
```
pyenv install <version number>
```
2. Activate Python version in current directory (with project)
```bash
pyenv local <version number>
```

### Install pipenv
1. Install pip env current environment
```bash
pip install pipenv
```
If you use system python maybe you need run pip with sudo or run pip3

### Install Pipenv environment
1. Run command
```bash
pipenv install
```
After installation is done, you have installed and configured virual environment with all dependency installed


## Preparing docker development environment

### Running docker-compose base environment
For base development processes, you may run
```bash
./compose <params>
```
script for get running database and other needed software.

Example:
```bash
./compose up -d
```
will run only **Database** and **RabbitMQ** with forwarded ports to localhost

### Running all environment in docker-compose
If you want to run all development environment in Docker, use _full_ argument instead, e.g:
```bash
./compose full <params>
```

Example:

```bash
./compose full up -d
```
will run all services, e.g. **Database**, **RabbitMQ**, **Celery**, **Flower**, **Application** with forwarded ports to localhost
