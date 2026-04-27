# envoy-cli

> A CLI tool to manage and diff environment variable configs across multiple deployment targets.

---

## Installation

```bash
pip install envoy-cli
```

Or install from source:

```bash
git clone https://github.com/yourname/envoy-cli.git && cd envoy-cli && pip install .
```

---

## Usage

Define your environment configs in a YAML file:

```yaml
# envoy.yaml
targets:
  staging:
    DATABASE_URL: postgres://staging-db/app
    DEBUG: "true"
  production:
    DATABASE_URL: postgres://prod-db/app
    DEBUG: "false"
```

Then use the CLI to inspect and compare targets:

```bash
# List all variables for a target
envoy list --target staging

# Diff two deployment targets
envoy diff staging production

# Export a target's config as a .env file
envoy export --target production --out .env.production
```

Example diff output:

```
~ DEBUG        staging="true"   production="false"
~ DATABASE_URL staging=postgres://staging-db/app   production=postgres://prod-db/app
```

---

## Commands

| Command       | Description                              |
|---------------|------------------------------------------|
| `list`        | List all env vars for a target           |
| `diff`        | Diff env vars between two targets        |
| `export`      | Export a target config to a `.env` file  |
| `validate`    | Check for missing or undefined variables |

---

## License

[MIT](LICENSE) © 2024 yourname