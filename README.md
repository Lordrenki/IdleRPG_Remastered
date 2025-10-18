# IdleRPG

[![CI](https://git.travitia.xyz/Kenvyra/IdleRPG/badges/current/pipeline.svg)](https://git.travitia.xyz/Kenvyra/IdleRPG)
[![Dockerhub](https://img.shields.io/badge/Pull%20IdleRPG-from%20Dockerhub-orange)](https://hub.docker.com/r/gelbpunkt/idlerpg)
[![okapi](https://img.shields.io/badge/Pull%20okapi-from%20Dockerhub-black)](https://hub.docker.com/r/gelbpunkt/okapi)
[![teatro](https://img.shields.io/badge/Pull%20teatro-from%20Dockerhub-green)](https://hub.docker.com/r/gelbpunkt/teatro)

This is the code for the IdleRPG Discord Bot.

You may [submit an issue](https://git.travitia.xyz/Kenvyra/IdleRPG/issues) or [open a pull request](https://git.travitia.xyz/Kenvyra/IdleRPG/merge_requests) at any time.

## License

The IdleRPG Project is licensed under the terms of the [GNU Affero General Public License 3.0](https://git.travitia.xyz/Kenvyra/IdleRPG/blob/current/LICENSE) ("AGPL"). It is a GPLv3 with extra clause for use over networks (see section 13).

[AGPL for humans](<https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)>).

## Running it

### Quick start with Docker Compose

1. Copy the example environment file:

   ```sh
   cp .env.example .env
   ```

2. Generate `config.toml` with the interactive helper. It walks through the required Discord and database credentials and writes a validated configuration file for you:

   ```sh
   python scripts/configure.py
   ```

   You can re-run the helper at any time to update secrets or optional integrations.

3. Edit `.env` to include your Discord bot token and any database credentials the compose stack should provision for you. Every field in the `[database]` block of the generated `config.toml` accepts environment variables, so you can keep the file under version control and inject secrets at runtime if preferred.

4. Launch the stack:

   ```sh
   docker compose up --build
   ```

By default the compose file provisions PostgreSQL and Redis containers and shares credentials with IdleRPG through environment variables. To point IdleRPG at hosted services instead, replace or remove the local `POSTGRES_*`/`REDIS_*` entries in `.env`, set `DATABASE_URL` or provider-specific variables for a Neon or Supabase instance, and provide a `REDIS_URL`/`UPSTASH_REDIS_URL` for providers such as Upstash. Leaving those variables set to the defaults continues to use the local containers.

### Initialize the schema

Once PostgreSQL is reachable you can bootstrap the schema with a single helper:

```sh
python scripts/init_db.py
```

Use `--config` and `--schema` to target different files if required.

### Managed Postgres and Redis options

IdleRPG's configuration loader automatically understands common connection strings:

- **Neon / Supabase** &mdash; Export `DATABASE_URL`, `POSTGRES_URL`, or provider-specific variables (user, password, host, port) and the loader will split them into the fields IdleRPG expects.
- **Upstash Redis** &mdash; Provide `REDIS_URL` or `UPSTASH_REDIS_URL` and the bot will connect over TLS with the correct password and database index.

These environment variables can be placed directly in `.env` or in your deployment platform's secret manager without altering `config.toml`.

### Interactive configuration for manual deployments

Outside Docker Compose you can still run the helper before starting the launcher:

```sh
python scripts/configure.py --config /path/to/config.toml
```

The script validates connection strings, enforces the presence of required PostgreSQL and Redis credentials, and ensures IdleRPG can authenticate with Discord before you launch the bot.

### Legacy Podman workflow

The original Podman scripts remain available for contributors who prefer that toolchain. Development instances will wipe storage when stopped.

```sh
git clone https://git.travitia.xyz/Kenvyra/IdleRPG.git
cd IdleRPG
./scripts/beta.sh
podman build -t idlerpg:latest .
podman run --rm -it --name idlerpg --pod idlerpgbeta -v $(pwd)/config.py:/idlerpg/config.py:Z idlerpg:latest
```

Permanent hosting scripts (`./scripts/setup.sh`) are still unsupported and may require manual adjustments.

## Utility

IdleRPG uses [black](https://github.com/ambv/black), [flake8](https://github.com/PyCQA/flake8) and [isort](https://github.com/timothycrosley/isort) for code style. Please always run `./scripts/format.sh` before submitting a pull request and fix any problems.

`./scripts/dumpdb.sh db_name` will update the database scheme from the postgres container.
