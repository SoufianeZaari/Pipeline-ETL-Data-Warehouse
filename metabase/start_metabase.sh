#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_JAR="${PROJECT_DIR}/metabase/metabase.jar"
TARGET_DIR="${HOME}/DATAEng/mexora_metabase"
TARGET_JAR="${TARGET_DIR}/metabase.jar"
LOG_FILE="${TARGET_DIR}/metabase.log"
PORT="${MB_JETTY_PORT:-3000}"
DOWNLOAD_URL="https://downloads.metabase.com/latest/metabase.jar"

log() {
  printf '[metabase] %s\n' "$*"
}

fail() {
  printf '[metabase][ERROR] %s\n' "$*" >&2
  exit 1
}

port_is_open() {
  ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(:|\\.)${PORT}$"
}

download_metabase() {
  log "metabase.jar source introuvable, téléchargement depuis ${DOWNLOAD_URL}"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 -o "${TARGET_JAR}" "${DOWNLOAD_URL}"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "${TARGET_JAR}" "${DOWNLOAD_URL}"
  else
    fail "Ni curl ni wget n'est installé. Installe curl ou place metabase.jar dans ${SOURCE_JAR}."
  fi
}

trap 'fail "Erreur à la ligne ${LINENO}. Consultez ${LOG_FILE} si Metabase a commencé à démarrer."' ERR

mkdir -p "${TARGET_DIR}"
: > "${LOG_FILE}"

if ! command -v java >/dev/null 2>&1; then
  fail "Java n'est pas installé. Installez-le avec : sudo apt install openjdk-21-jre -y"
fi

log "Version Java détectée :"
java -version 2>&1 | tee -a "${LOG_FILE}"

if [[ -f "${SOURCE_JAR}" ]]; then
  log "Copie du JAR vers un chemin sans espace : ${TARGET_JAR}"
  cp -f "${SOURCE_JAR}" "${TARGET_JAR}"
elif [[ -s "${TARGET_JAR}" ]]; then
  log "JAR source absent, utilisation de la copie existante : ${TARGET_JAR}"
else
  download_metabase | tee -a "${LOG_FILE}"
fi

[[ -s "${TARGET_JAR}" ]] || fail "metabase.jar est absent ou vide : ${TARGET_JAR}"

if port_is_open; then
  log "Le port ${PORT} est déjà ouvert. Metabase semble déjà démarré."
  log "Metabase disponible sur http://localhost:${PORT}"
  exit 0
fi

cd "${TARGET_DIR}"
log "Démarrage de Metabase depuis : ${TARGET_DIR}"
log "Logs : ${LOG_FILE}"

JAVA_CMD=(
  java
  --add-opens java.base/java.nio=ALL-UNNAMED
  -Duser.dir="${TARGET_DIR}"
  -jar "${TARGET_JAR}"
)

if command -v setsid >/dev/null 2>&1; then
  setsid "${JAVA_CMD[@]}" >> "${LOG_FILE}" 2>&1 < /dev/null &
else
  nohup "${JAVA_CMD[@]}" >> "${LOG_FILE}" 2>&1 < /dev/null &
fi

METABASE_PID="$!"
log "PID Metabase : ${METABASE_PID}"

for _ in $(seq 1 90); do
  if ! kill -0 "${METABASE_PID}" 2>/dev/null; then
    tail -80 "${LOG_FILE}" >&2 || true
    fail "Metabase s'est arrêté pendant le démarrage."
  fi
  if port_is_open; then
    sleep 3
    if ! kill -0 "${METABASE_PID}" 2>/dev/null; then
      tail -80 "${LOG_FILE}" >&2 || true
      fail "Metabase a ouvert le port ${PORT} puis s'est arrêté."
    fi
    log "Metabase disponible sur http://localhost:${PORT}"
    exit 0
  fi
  sleep 2
done

tail -80 "${LOG_FILE}" >&2 || true
fail "Metabase n'a pas ouvert le port ${PORT} dans le délai prévu."
