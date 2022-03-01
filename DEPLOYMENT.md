## Deployment

Deployment uses `dokku` and is deployed to our `dokku2` instance.

## Deployment instructions

### Create app

On dokku2, as the `dokku` user:

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

### Manually deploying

Merges to the `main` branch will trigger an auto-deploy via GitHub actions.

Note this deploys by building the prod docker image (see `docker/docker-compose.yaml`) and using the dokku [git:from-image](https://dokku.com/docs/deployment/methods/git/#initializing-an-app-repository-from-a-docker-image) command.

To deploy manually:

```
# build prod image locally
just docker-build prod

# tag image and push
docker tag output-explorer ghcr.io/opensafely-core/output-explorer:latest
docker push ghcr.io/opensafely-core/output-explorer:latest

# get the SHA for the latest image
SHA=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/opensafely-core/output-explorer:latest)
```

On dokku2, as the `dokku` user:
```
dokku$ dokku git:from-image output-explorer <SHA>
```

### extras

Requires the `sentry-webhook` and `letsencrypt` plugins.

```sh
# Check plugins installed:
dokku$ dokku plugin:list

# enable letsencrypt (must be run as root)
root$ dokku config:set --no-restart output-explorer DOKKU_LETSENCRYPT_EMAIL=<e-mail>
root$ dokku letsencrypt:enable output-explorer

# turn on/off HTTP auth (also requires restarting the app)
dokku$ dokku http-auth:on output-explorer <user> <password>
dokku$ dokku http-auth:off output-explorer
```
