# OpenSAFELY Output Explorer

This is a Django app providing a location for viewing and exploring OpenSAFELY outputs,
both publicly available and content that limits access based on a user's NHS organisation membership.
Some content is publicly accessible; private content is accessed via authentication with
NHS Identity via Open ID Connect.  Authorisation is based on the NHS
associated organisation information retrieved from NHS Identity.


## Deployment
Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku2` instance.

## Deployment instructions

### Create app
```
dokku$ dokku apps:create output-explorer
dokku$ dokku domains:add output-explorer output-explorer.opensafely.org
dokku$ dokku git:set output-explorer deploy-branch main
```

### Create storage for sqlite db
```
dokku$ mkdir /var/lib/dokku/data/storage/output-explorer
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/output-explorer
dokku$ dokku storage:mount output-explorer /var/lib/dokku/data/storage/output-explorer/:/storage
```

### Configure app
```
dokku$ dokku config:set output-explorer BASE_URL='https://output-explorer.opensafely.org'
dokku$ dokku config:set output-explorer DATABASE_URL='sqlite:////storage/db.sqlite3'
dokku$ dokku config:set output-explorer SECRET_KEY='xxx'
dokku$ dokku config:set output-explorer SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku$ dokku config:set output-explorer SENTRY_ENVIRONMENT='production'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_KEY='xxx'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_SECRET='xxx'
dokku$ dokku config:set output-explorer SOCIAL_AUTH_NHSID_API_URL='xxx'
dokku$ dokku config:set output-explorer SHOW_LOGIN=False
```

### Deploy by manually pushing
```
local$ git clone git@github.com:opensafely-core/output-explorer.git
local$ cd output-explorer
local$ git remote add dokku dokku@MYSERVER:output-explorer
local$ git push dokku main
```

### extras
```
dokku letsencrypt output-explorer
dokku plugin:install sentry-webhook
```

## Local development

### Install system requirements
```
# macOS
brew install just

# Linux
apt install just

# Add completion for your shell. E.g. for bash:
just --completion bash > just.bash
source just.bash

# Show all available commands
just #  shortcut for just --list
```

### Run local development server
#### Set up local dev env
```
just dev-config
just setup
```
#### Run local django server
```
just run
```
Access at http://localhost:8000

Login with one of the test user accounts (see Bitwarden entry for password):
- 555036632103
- 555036633104
- 555036634105

#### Run tests
```
# all tests and coverage
just test

# specific test
just test-only <path/to/test>
```
