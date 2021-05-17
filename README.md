# OpenSAFELY Output Explorer

This is a Django app providing a location for viewing and exploring OpenSAFELY outputs, both publicly available and content that limits access based on a user's NHS organisation membership.

Some content is publicly accessible; private content is accessed via authentication with NHS Identity via Open ID Connect. Authorisation is based on the NHS associated organisation information retrieved from NHS Identity.

## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku2` instance.

## Deployment instructions

### Create app

```sh
dokku$ dokku apps:create output-explorer
dokku$ dokku domains:add output-explorer output-explorer.opensafely.org
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
dokku$ dokku config:set output-explorer BASE_URL='https://output-explorer.opensafely.org'
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

### Deploy by manually pushing

```sh
local$ git clone git@github.com:opensafely-core/output-explorer.git
local$ cd output-explorer
local$ git remote add dokku dokku@MYSERVER:output-explorer
local$ git push dokku main
```

You may need to add your ssh key to dokku's authorised keys; use the method described [here](https://dokku.com/docs/deployment/user-management/)

### extras

```sh
dokku letsencrypt:enable output-explorer
dokku plugin:install sentry-webhook
```

## Local development

### Prerequisites:

- **Python and Pip**
- **Node.js v16**
  - macOS / Linux / WSL: [fnm](https://github.com/Schniz/fnm)
  - Windows: [NVM for Windows](https://github.com/coreybutler/nvm-windows)
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

### Run local development server

#### Install Node.js dependencies and build assets

```sh
# Set your Node.js version
fnm use # using fnm
nvm use # using nvm

# Install dependencies
npm ci

# Build assets
npm run build
```

#### Set up local dev env

```sh
just dev-config
just setup
```

#### Run local django server

```sh
just run
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

# specific test
just test-only <path/to/test>
```

#### CSS and JS local development

This project uses [Vite](https://vitejs.dev/) which allows for local hot-module reloading via a development server. To run the Vite server locally, after completing the local dev env setup:

1. Set `DJANGO_VITE_DEV_MODE = True` in `output_explorer/settings.py`
2. Open a terminal and run Django with `just run`
3. Open a new terminal tab or window
4. Run `npm run dev` to start the vite server
5. Any changes you make in the `assets/` folder will now be updated without requiring a page refresh
