# Getting Started

This guide walks you through setting up your development environment from scratch. By the end, you will have the project running locally and be ready to contribute.

## Prerequisites

You need to install the following tools. Follow the sections below in order.

### 1. Install Git and set up GitHub

Git is the version control system used to track changes. GitHub hosts the repository.

**Install Git:**

- Download from <https://git-scm.com/downloads> and run the installer
- Accept the defaults; when asked about the default editor, choose VS Code if available

**Set up GitHub:**

1. Create a free account at <https://github.com> if you don't have one
2. Open a terminal (PowerShell or Command Prompt) and configure Git:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

**Clone the repository:**

```bash
git clone https://github.com/realslimslaney/soa-weather.git
cd soa-weather
```

### 2. Install VS Code

VS Code is the recommended editor for this project.

1. Download from <https://code.visualstudio.com/>
2. Run the installer — check "Add to PATH" when prompted
3. Open VS Code, then open the `soa-weather` folder (`File > Open Folder`)

**Recommended extensions** (VS Code will prompt you to install these if configured):

- Python (`ms-python.python`)
- Ruff (`charliermarsh.ruff`)

### 3. Install Python

This project requires Python 3.12 or newer.

1. Download from <https://www.python.org/downloads/>
2. **Important:** Check "Add Python to PATH" during installation
3. Verify in a new terminal:

```bash
python --version
```

### 4. Install uv

uv is a fast Python package manager that replaces pip and virtualenv.

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

### 5. Install just

just is a command runner (like make, but simpler). We use it for common development tasks.

**Windows (pick one):**

Chocolatey:

```powershell
choco install just
```

WinGet (built into Windows 11):

```powershell
winget install Casey.Just
```

Scoop:

```powershell
scoop install just
```

**macOS:**

```bash
brew install just
```

**Linux:**

```bash
# Debian/Ubuntu
sudo apt install just
# or use prebuilt binaries from https://github.com/casey/just/releases
```

Verify:

```bash
just --version
```

## Project Setup

With all prerequisites installed, set up the project:

```bash
# Install all dependencies (creates a virtual environment automatically)
uv sync

# Install pre-commit hooks (runs linting and formatting on each commit)
just install-hooks

# Verify everything works
just check
```

This will lint, format-check, and run the test suite.

## Data Directory

By default, weather data is stored at `C:/Data/SOA_Weather` on Windows and `~/Data/SOA_Weather` on macOS/Linux. The folder is created automatically the first time you run a script.

To use a custom location, copy `.env.example` to `.env` and set your path:

```bash
cp .env.example .env
# then edit .env and uncomment/set SOA_WEATHER_DATA
```

Or set the environment variable directly:

```bash
export SOA_WEATHER_DATA=/path/to/your/data   # macOS/Linux
set SOA_WEATHER_DATA=D:\your\data             # Windows
```

## Running Scripts

Use `uv run` to execute scripts inside the managed environment:

```bash
uv run python scripts/read_station_data.py
```

## Next Steps

- Read [contributing.md](contributing.md) for workflow guidelines
- Explore the `scripts/` folder for existing analyses
- Check the [NOAA CDO datasets page](https://www.ncei.noaa.gov/cdo-web/datasets) for available weather data
