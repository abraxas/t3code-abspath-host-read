#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

LABEL="T3-F01-ABSPATH"
WITNESS="t3f01w8k2"
PIN="61c3794c32b0eeebfac09add43e403618c65d2d7"
REPO_URL="${T3_SRC_URL:-https://github.com/pingdotgg/t3code.git}"
LOOPBACK_PORT="18191"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-t3-f01-abs}"
export PYTHONUNBUFFERED=1

teardown() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"${LOOPBACK_PORT}" -sTCP:LISTEN -t 2>/dev/null | xargs kill 2>/dev/null || true
  fi
}

fail_setup() {
  local reason="$1"
  echo "FAIL ${LABEL} ${reason} ${WITNESS}" | tee poc-last-run.txt
  exit 1
}

trap teardown EXIT

mkdir -p lab-home tmp .tools workspace

if [[ ! -e src/.git ]]; then
  git clone --filter=blob:none --no-checkout "${REPO_URL}" src || fail_setup "clone-failed"
  git -C src fetch --depth 1 origin "${PIN}" || fail_setup "fetch-failed"
  git -C src checkout --detach FETCH_HEAD || fail_setup "checkout-failed"
fi

got="$(git -C src rev-parse HEAD)"
if [[ "${got}" != "${PIN}" ]]; then
  fail_setup "pin-mismatch"
fi

LAB_HOME="${PWD}/lab-home"
export T3CODE_HOME="${LAB_HOME}"
export TMPDIR="${PWD}/tmp"
export npm_config_cache="${PWD}/lab-home/.npm"
export PNPM_HOME="${PWD}/lab-home/.pnpm"
export XDG_CACHE_HOME="${LAB_HOME}/.cache"
mkdir -p "${LAB_HOME}" "${npm_config_cache}" "${PNPM_HOME}" "${XDG_CACHE_HOME}" "${TMPDIR}"

PATH_PREFIX="${PWD}/.tools/node_modules/.bin:${PNPM_HOME}"
export PATH="${PATH_PREFIX}:${PATH}"

if ! command -v pnpm >/dev/null 2>&1; then
  if command -v corepack >/dev/null 2>&1; then
    corepack enable || true
    corepack prepare pnpm@12.14.0 --activate || fail_setup "install-failed"
  else
    npm install --prefix .tools pnpm@12.14.0 || fail_setup "install-failed"
  fi
fi

if ! command -v pnpm >/dev/null 2>&1; then
  fail_setup "install-failed"
fi

if [[ ! -d src/node_modules && ! -d src/apps/server/node_modules ]]; then
  (
    cd src
    pnpm install --frozen-lockfile --filter t3... --config.engine-strict=false
  ) || fail_setup "install-failed"
fi

if [[ ! -x src/apps/server/node_modules/.bin/vp && ! -x src/node_modules/.bin/vp ]]; then
  (
    cd src
    pnpm install --frozen-lockfile --filter t3... --config.engine-strict=false
  ) || fail_setup "install-failed"
fi

if [[ ! -x src/apps/server/node_modules/.bin/vp && ! -x src/node_modules/.bin/vp ]]; then
  fail_setup "install-failed"
fi

set +e
python3 ./poc.py | tee poc-last-run.txt
rc=${PIPESTATUS[0]}
set -e

if ! tail -n1 poc-last-run.txt 2>/dev/null | grep -qE "^(SUCCESS|FAIL) ${LABEL} "; then
  echo "FAIL ${LABEL} poc-exit=${rc} ${WITNESS}" >> poc-last-run.txt
  rc=1
fi

exit "${rc}"
