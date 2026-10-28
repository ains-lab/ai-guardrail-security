#!/usr/bin/env bash
# Linux/Bash: downloaded GGUF selector and single managed server lifecycle.
set -euo pipefail
BIN=${LLAMA_SERVER_BIN:-$HOME/tools/llama.cpp/build/bin/llama-server}
MODELS=${LLAMA_MODELS_DIR:-$HOME/models}
PORT=${LLAMA_PORT:-8080}
STATE=${LLAMA_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/llama-server-manager}
CTX=${LLAMA_CTX_SIZE:-4096}
LAYERS=${LLAMA_GPU_LAYERS:-99}
ALIAS=${LLAMA_ALIAS:-qwen2.5-7b}
WAIT=${LLAMA_START_TIMEOUT:-180}
fail() { printf '오류: %s\n' "$*" >&2; exit 1; }
help_text() {
    cat <<'HELP'
사용: scripts/llama-server.sh [menu|list|start [번호]|stop|restart [번호]|status|logs]
기본: ~/models의 GGUF, ~/tools/llama.cpp/build/bin/llama-server,
      127.0.0.1:8080, alias=qwen2.5-7b, ctx=4096, GPU layers=99.
환경 변수: LLAMA_SERVER_BIN, LLAMA_MODELS_DIR, LLAMA_PORT, LLAMA_STATE_DIR,
           LLAMA_CTX_SIZE, LLAMA_GPU_LAYERS, LLAMA_ALIAS, LLAMA_START_TIMEOUT.
다른 모델 선택 시 LLAMA_ALIAS 및 garak YAML의 target_name도 맞추세요.
stop/restart는 이 상태 폴더에서 직접 시작한 서버만 종료합니다.
HELP
}
[[ ${1:-} != --help && ${1:-} != -h ]] || { help_text; exit 0; }
for v in "$PORT" "$CTX" "$LAYERS" "$WAIT"; do
    [[ $v =~ ^[0-9]+$ ]] || fail '숫자 설정값이 잘못되었습니다.'
done
((PORT > 0 && PORT < 65536 && CTX > 0 && WAIT > 0)) || fail '포트/컨텍스트/대기시간 범위 오류'
command -v curl >/dev/null || fail 'curl 필요'
command -v python3 >/dev/null || fail 'python3 필요'
umask 077
mkdir -p "$STATE"
exec 9>"$STATE/lock"
flock -n 9 || fail '다른 관리 명령이 실행 중입니다.'
PIDFILE=$STATE/process
LOG=$STATE/server.log
# /proc start-time prevents signaling a recycled PID; exe prevents other binaries.
identity() {
    [[ -r /proc/$1/stat ]] || return 1
    python3 - "$1" <<'PY'
import sys
from pathlib import Path
try:
    text = Path('/proc', sys.argv[1], 'stat').read_text()
    fields = text[text.rfind(')') + 2:].split()
    if fields[0] == 'Z':
        raise ValueError('zombie')
    print(fields[19])
except (OSError, ValueError):
    sys.exit(1)
PY
}
owned() {
    [[ -f $PIDFILE ]] || return 1
    read -r pid stamp < "$PIDFILE" || return 1
    [[ $pid =~ ^[0-9]+$ && $stamp =~ ^[0-9]+$ ]] || return 1
    [[ $(identity "$pid") == "$stamp" ]] || return 1
    [[ $(readlink -f "/proc/$pid/exe") == $(readlink -f "$BIN") ]]
}
scan() {
    models=()
    [[ -d $MODELS ]] || fail "모델 폴더 없음: $MODELS"
    while IFS= read -r -d '' file; do
        # Only first split is offered; all other splits load automatically.
        [[ ! $file =~ -[0-9]{5}-of-[0-9]{5}\.gguf$ || $file =~ -00001-of-[0-9]{5}\.gguf$ ]] || continue
        models+=("$file")
    done < <(find "$MODELS" -type f -name '*.gguf' -print0 | sort -z)
    ((${#models[@]})) || fail 'GGUF 모델이 없습니다.'
}
show_models() {
    scan
    for i in "${!models[@]}"; do printf '%d) %s\n' "$((i+1))" "${models[i]}"; done
}
choose() {
    show_models
    local choice=${1:-}
    if [[ -z $choice ]]; then
        read -r -p '모델 번호: ' choice || fail '모델 번호를 지정하세요.'
    fi
    [[ $choice =~ ^[1-9][0-9]*$ ]] || fail '유효한 번호가 아닙니다.'
    ((${#choice} < 8)) || fail '번호 범위 오류'
    ((choice <= ${#models[@]})) || fail '번호 범위 오류'
    model=${models[choice-1]}
    if [[ $model =~ -00001-of-([0-9]{5})\.gguf$ ]]; then
        total=$((10#${BASH_REMATCH[1]}))
        for ((i=1;i<=total;i++)); do
            printf -v suffix '%05d-of-%05d.gguf' "$i" "$total"
            [[ -s ${model%-00001-of-*}-$suffix ]] || fail "모델 조각 누락: $suffix"
        done
    fi
}
stop_server() {
    if ! owned; then
        printf '관리 중인 서버가 없습니다. 기존 외부 서버는 종료하지 않습니다.\n'
        return 0
    fi
    kill -TERM "$pid"
    for ((i=0;i<60;i++)); do
        if ! owned; then rm -f "$PIDFILE"; printf '중지 완료\n'; return 0; fi
        sleep 1
    done
    fail '종료 대기시간 초과. 강제 종료하지 않았습니다.'
}
start_server() {
    [[ -x $BIN ]] || fail "실행 파일 없음: $BIN"
    owned && fail "이미 관리 중인 서버가 있습니다: PID $pid"
    choose "${1:-}"
    python3 - "$PORT" <<'PY'
import socket, sys
with socket.socket() as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('127.0.0.1', int(sys.argv[1])))
    except OSError:
        sys.exit('포트 사용 중: 기존 서버를 확인하세요. 자동 종료하지 않습니다.')
PY
    nohup "$BIN" --model "$model" --alias "$ALIAS" --n-gpu-layers "$LAYERS" \
        --ctx-size "$CTX" --parallel 1 --host 127.0.0.1 --port "$PORT" \
        >"$LOG" 2>&1 < /dev/null 9>&- &
    pid=$!
    stamp=$(identity "$pid") || fail "시작 실패. 로그: $LOG"
    printf '%s %s\n' "$pid" "$stamp" > "$PIDFILE"
    for ((i=0;i<WAIT;i++)); do
        owned || fail "서버 종료됨. 로그: $LOG"
        if curl --noproxy '*' -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
            printf '시작 완료: PID %s / http://127.0.0.1:%s/v1 / alias=%s\n로그: %s\n' "$pid" "$PORT" "$ALIAS" "$LOG"
            return 0
        fi
        sleep 1
    done
    stop_server
    fail "시작 대기시간 초과. 로그: $LOG"
}
action=${1:-menu}
if [[ $action == menu ]]; then
    printf '1) 시작 (모델 선택)\n2) 중지\n3) 재시작 (모델 선택)\n4) 상태\n5) 모델 목록\n'
    read -r -p '작업 번호: ' item
    case $item in 1) action=start;; 2) action=stop;; 3) action=restart;; 4) action=status;; 5) action=list;; *) fail '작업 번호 오류';; esac
fi
case $action in
    list) show_models;;
    start) start_server "${2:-}";;
    stop) stop_server;;
    restart)
        # Validate selection before taking down a running server.
        choose "${2:-}"
        selected=$model
        index=1
        for file in "${models[@]}"; do [[ $file == "$selected" ]] && break; index=$((index+1)); done
        stop_server
        start_server "$index"
        ;;
    status)
        if owned; then
            printf '관리 중: PID %s\n' "$pid"
            curl --noproxy '*' -fsS --max-time 3 "http://127.0.0.1:$PORT/health"
            printf '\n'
        else printf '관리 중인 서버 없음 (다른 방식으로 시작한 서버는 별도 확인)\n'; fi
        ;;
    logs) [[ ! -f $LOG ]] || tail -n 60 "$LOG";;
    *) help_text; exit 2;;
esac
