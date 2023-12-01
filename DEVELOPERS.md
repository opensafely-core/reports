# Notes for developers

## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku3` instance (see [dokku docs](https://bennettinstitute-team-manual.pages.dev/tools-systems/dokku/)).

## Local development

### Prerequisites:

- **Python v3.10.x**
- **Pip**
- **Node.js v16.x** ([fnm](https://github.com/Schniz/fnm#installation) is recommended)
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

**Build the assets:**

See the [Compiling assets](#compiling-assets) section.

#### Set up/update local dev environment

```sh
just dev-setup
```

### Run local development server

The development server can be run locally, as described below, or in [docker](#using-docker-for-development-and-tests).

#### Run local django server

```sh
just run
```

#### Delete local database and cache and repopulate db
```sh
just dev-reset
```

Access at http://localhost:8000


#### Run tests

```sh
# all tests and coverage
just test

# run specific test with usual pytest syntax
just test <path/to/test>::<test name>
```

#### CSS and JS local development

This project uses [Vite](https://vitejs.dev/), a modern build tool and development server, to build the frontend assets.
Vite integrates into the Django project using the [django-vite](https://github.com/MrBin99/django-vite) package.

Vite works by compiling JavaScript files, and outputs a manifest file, the JavaScript files, and any included assets such as stylesheets or images.

Vite adds all JavaScript files to the page using [ES6 Module syntax](https://caniuse.com/es6-module).
For legacy browsers, this project is utilising the [Vite Legacy Plugin](https://github.com/vitejs/vite/tree/main/packages/plugin-legacy) to provide a fallback using the [module/nomodule pattern](https://philipwalton.com/articles/deploying-es2015-code-in-production-today/).

For styling this project uses [Scss](https://www.npmjs.com/package/sass) to compile the stylesheets, and then [PostCSS](https://github.com/postcss/postcss) for post-processing.

## Running the local asset server

Vite has a built-in development server which will serve the assets and reload them on save.

To run the Vite server locally, after completing the local dev env setup:

1. Set `DJANGO_VITE_DEV_MODE = True` in `reports/settings.py`
2. Open a terminal and run Django with `just run`
3. Open a new terminal tab or window
4. Run `npm run dev` to start the vite server
5. Any changes you make in the `assets/` folder will now be updated without requiring a page refresh

This will start the Vite dev server at [localhost:3000](http://localhost:3000/) and inject the relevant scripts into the Django templates.

### Compiling assets

To view the compiled assets:

1. Update the `.env` file to `DJANGO_VITE_DEV_MODE=False`
2. Run `just assets-rebuild`

Vite builds the assets and outputs them to the `assets/dist` folder.

[Django Staticfiles app](https://docs.djangoproject.com/en/3.2/ref/contrib/staticfiles/) then collects the files and places them in the `staticfiles/assets` folder, with the manifest file located at `staticfiles/manifest.json`.

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


## Rotating the GitHub token
1. Log into the `opensafely-readonly` GitHub account (credentials are in Bitwarden).
1. Got to the [Personal access tokens (classic) page](https://github.com/settings/tokens).
1. Click on `reports-private-repo-token`.
1. Click "Regenerate token".
1. Set the expiry to 90 days.
1. Copy the new token.
1. ssh into `dokku3.ebmdatalab.net`
1. Run: `dokku config:set reports GITHUB_TOKEN=<the new token>`
