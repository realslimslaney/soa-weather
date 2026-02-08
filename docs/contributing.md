# Contributing

How to contribute to the soa-weather project.

## Workflow

1. Create a branch for your work:

```bash
git checkout -b your-branch-name
```

2. Make your changes. Run checks frequently:

```bash
just check
```

3. Commit your changes with a clear message:

```bash
git add <files>
git commit -m "Brief description of changes"
```

4. Push and open a pull request:

```bash
git push -u origin your-branch-name
```

Then open a PR on GitHub. Fill out the PR template.

## Code Style

- **Formatter/linter:** ruff (runs automatically in CI)
- **Line length:** 100 characters
- **Imports:** sorted by ruff (`isort` rules)
- **Polars numeric types:** default to `Float64` and `Int64` — avoid 32-bit types unless there is a specific memory constraint
- Auto-format before committing: `just format`

## Project Structure

| Directory | Purpose |
|---|---|
| `src/soa_weather/` | Shared package — importable modules and utilities |
| `scripts/` | Analysis scripts — each script is a standalone entry point |
| `tests/` | Test suite — run with `just test` |
| `docs/` | Documentation |

## Adding Dependencies

Add runtime dependencies:

```bash
uv add <package-name>
```

Add dev-only dependencies:

```bash
uv add --dev <package-name>
```
