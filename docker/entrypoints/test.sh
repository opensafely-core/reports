#!/bin/bash

set -euo pipefail

just --no-deps assets-collect

"$@"
