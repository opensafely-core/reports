# OpenSAFELY Dashboards

This is a Django app providing a location for data content that limits
access based on a user's NHS organisation membership.  Some content is
publicly accessible; private content is accessed via authentication with
NHS Identity via Open ID Connect.  Authorisation is based on the NHS
associated organisation information retrieved from NHS Identity.

## Local development

### Install requirements
```
pip install -r requirements.txt
```

### Install pre-commit hooks
```
pre-commit install
```

### Setup environment variables
Copy `nhsid_openid_connect/dotenv-sample` to `nhsid_openid_connect/.env`
and update the `SOCIAL_AUTH_NHSID_KEY` and `SOCIAL_AUTH_NHSID_SECRET`
variables.

### Run local django server
```
./manage.py runserver
```
Access at http://localhost:8000

Login with one of the test user accounts:
- 555036632103
- 555036633104
- 555036634105

The password for all three is welcomecakebanana

### Run tests
```
pytest tests/
```
