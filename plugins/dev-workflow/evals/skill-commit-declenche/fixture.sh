#!/usr/bin/env bash
set -euo pipefail
cp -r "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_fixtures/bookshelf/." .
git init -q -b main . && git add -A && git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "feat: bookshelf"
printf "\nexport const VERSION = 2;\n" >> src/rates.js
