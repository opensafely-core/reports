# Notes for developers

## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku2` instance (see [deployment notes](DEPLOYMENT.md)).

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
