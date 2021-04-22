# OpenSAFELY Short Data Reports

This is a Django app providing a location for data content that limits
access based on a user's NHS organisation membership.  Some content is
publicly accessible; private content is accessed via authentication with
NHS Identity via Open ID Connect.  Authorisation is based on the NHS
associated organisation information retrieved from NHS Identity.

## Local development

### Install system requirements
```
# OSX
brew install just

# Linux
apt install just

# Add completion for your shell. E.g. for bash:
just --completion bash > just.bash
source just.bash

# Show all available commands
just #  shortcut for just --list
```

### Set up local dev env
```
just dev-config
just setup
```

### Run local django server
```
just run
```
Access at http://localhost:8000

Login with one of the test user accounts:
- 555036632103
- 555036633104
- 555036634105

The password for all three is welcomecakebanana

### Run tests
```
# all tests and coverage
just test

# specific test
just test-only <path/to/test>
```
