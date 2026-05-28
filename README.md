# waguri

a small discord bot

## requirements

- python 3.14+
- [uv](https://docs.astral.sh/uv/)
- docker + docker compose (optional)

## running locally

```bash
uv sync
uv run main.py
```

## running with docker

```bash
docker compose up --build
```

## env vars

- `DISCORD_TOKEN`
- `waguri_dev`: if set, loads the [`dev`](./cogs/dev.py) cog.
- `waguri_prod`: if set, syncs application commands globally on startup.
