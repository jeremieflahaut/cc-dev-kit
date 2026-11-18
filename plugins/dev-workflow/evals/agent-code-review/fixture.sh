#!/usr/bin/env bash
set -euo pipefail
cp -r "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_fixtures/bookshelf/." .
