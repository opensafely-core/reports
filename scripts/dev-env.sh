#!/bin/bash
set -euo pipefail
target="$1"

if ! command -v bw > /dev/null; then
    echo "You need the bitwarden cli tool installed:"
    echo
    echo "    https://bitwarden.com/help/article/cli/#download-and-install"
    echo
    exit 1
fi

session_from_env=${BW_SESSION-"not-found"}

if (test $session_from_env = "not-found"); then
    echo "Unlocking bitwarden..."
    BW_SESSION=$(bw unlock --raw)
    export BW_SESSION
fi

GH_DEV_TOKEN_BW_ID=10242708-234a-4162-982f-ace700ee5c53
NHSID_DEV_TOKEN_BW_ID=d56dc9f4-d732-45d9-90fd-ad1200b7e27c

write() {
    local name="$1"
    local value="$2"
    sed -i"" -e "s/$name=.*/$name=$value/" "$target"
}

write GITHUB_TOKEN "$(bw get password $GH_DEV_TOKEN_BW_ID)"
write SOCIAL_AUTH_NHSID_KEY "$(bw get username $NHSID_DEV_TOKEN_BW_ID)"
write SOCIAL_AUTH_NHSID_SECRET "$(bw get password $NHSID_DEV_TOKEN_BW_ID)"
