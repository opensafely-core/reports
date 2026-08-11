#!/bin/bash

set -euo pipefail

just manage migrate
just manage ensure_groups
just manage createcachetable

exec just prod-server
