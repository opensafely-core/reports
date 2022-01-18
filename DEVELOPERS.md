# Notes for developers

## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku2` instance.

## Deployment instructions

### Create app

```sh
dokku$ dokku apps:create output-explorer
dokku$ dokku domains:add output-explorer reports.opensafely.org
dokku$ dokku git:set output-explorer deploy-branch main
```

### Create storage for sqlite db

```sh
dokku$ mkdir /var/lib/dokku/data/storage/output-explorer
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/output-explorer
dokku$ dokku storage:mount output-explorer /var/lib/dokku/data/storage/output-explorer/:/storage
```

### Configure app

```sh
dokku$ dokku config:set output-explorer BASE_URL='https://reports.opensafely.org'
dokku$ dokku config:set output-explorer DATABASE_URL='sqlite:////storage/db.sqlite3'
dokku$ dokku config:set output-explorer SECRET_KEY='xxx'
dokku$ dokku config:set output-explorer SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku$ dokku config:set output-explorer SENTRY_ENVIRONMENT='production'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_KEY='xxx'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_SECRET='xxx'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_API_URL='xxx'
dokku$ dokku config:set output-explorer GITHUB_TOKEN='xxx'
dokku$ dokku config:set output-explorer SHOW_LOGIN=False
```


### Manually pushing

Merges to the `main` branch will trigger an auto-deploy via GitHub actions.

Note this deploys by building the prod docker image (see `docker/docker-compose.yaml`) and using the dokku [git:from-image](https://dokku.com/docs/deployment/methods/git/#initializing-an-app-repository-from-a-docker-image) command.


### extras

```sh
dokku$ dokku letsencrypt:enable output-explorer
dokku$ dokku plugin:install sentry-webhook

# turn on/off HTTP auth (also requires restarting the app)
dokku$ dokku http-auth:on output-explorer <user> <password>
dokku$ dokku http-auth:off output-explorer
```

## Local development

### Prerequisites:

- **Python v3.10.x**
- **Pip**
- **[fnm](#install-fnm)**
- **[Just](#install-just)**

### Install just

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Add completion for your shell. E.g. for bash:
source <(just --completions bash)

# Show all available commands
just #  shortcut for just --list
```

### Install fnm

See https://github.com/Schniz/fnm#installation.

### Run local development server

The development server can be run locally, as described below, or in [docker](#using-docker-for-development-and-tests).

#### Set up/update local dev environment

```sh
just dev-setup
```

#### Run local django server

```sh
just run
```

#### Delete local database and cache and repopulate db
```sh
just dev-reset
```

Access at http://localhost:8000

Login with one of the test user accounts (see Bitwarden entry "Output Explorer NHS Identity Open ID Connect" for password):

- 555036632103
- 555036633104
- 555036634105

#### Run tests

```sh
# all tests and coverage
just test

# run specific test with usual pytest syntax
just test <path/to/test>::<test name>
```

#### CSS and JS local development

This project uses [Vite](https://vitejs.dev/) which allows for local hot-module reloading via a development server. To run the Vite server locally, after completing the local dev env setup:

1. Set `DJANGO_VITE_DEV_MODE = True` in `output_explorer/settings.py`
2. Open a terminal and run Django with `just run`
3. Open a new terminal tab or window
4. Run `npm run dev` to start the vite server
5. Any changes you make in the `assets/` folder will now be updated without requiring a page refresh


### Using docker for development and tests

Run a local development server in docker:

```sh
just docker-serve
```

Run the tests in docker
```sh
just docker-test
```

To run named test(s) or pass additional args, pass paths and args as you normally would to pytest:
```sh
just docker-test tests/reports/test_models.py::test_report_model_validation -k some-mark --pdb
```

Run a command in the dev docker containter
```sh
just docker-run <command>
```
