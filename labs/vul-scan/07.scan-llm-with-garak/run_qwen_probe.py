"""기존 로컬 Qwen YAML로 garak 프로브를 조회·선택·실행한다.

예:
  .venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py
  .../run_qwen_probe.py --list --probe-spec encoding
  .../run_qwen_probe.py --probe-spec web_injection.MarkdownImageExfil
  .../run_qwen_probe.py --probe-spec encoding.InjectBase64 --dry-run

프로브 출력은 렌더링하지 않는다. 설치된 프로브 중에는 별도 모델/네트워크/
패키지가 필요한 것도 있으므로 목록에 있다는 것이 실행 성공을 보장하지 않는다.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import uuid


HERE = Path(__file__).resolve().parent


def normalize_spec(value):
    """단일 프로브 또는 모듈을 garak 0.17의 --spec 형식으로 바꾼다."""
    value = value.strip()
    if not re.fullmatch(r"(?:probes\.)?[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)?", value):
        raise ValueError("모듈 또는 모듈.클래스 한 개를 지정하세요 (예: encoding.InjectBase64).")
    return value if value.startswith("probes.") else "probes." + value


def discover(spec=None):
    command = [sys.executable, "-m", "garak", "--list_probes"]
    if spec:
        command += ["--spec", spec]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    # ANSI 색상과 garak 시작 배너를 제외한 실제 플러그인 이름만 사용한다.
    text = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    return sorted(set(re.findall(r"^probes:\s+([A-Za-z_0-9]+\.[A-Za-z_0-9]+)", text, re.MULTILINE)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probe-spec", help="프로브 클래스 또는 모듈 (probes. 접두사는 생략 가능)")
    parser.add_argument("--list", action="store_true", help="설치된 프로브 목록만 조회")
    parser.add_argument("--dry-run", action="store_true", help="선택을 검증하고 실행 명령만 표시")
    parser.add_argument("--config", type=Path, default=HERE / "probe-qwen-local.yaml")
    args = parser.parse_args(argv)
    try:
        spec = normalize_spec(args.probe_spec) if args.probe_spec else None
        probes = discover(spec)
        if not probes:
            parser.error("일치하는 설치된 프로브가 없습니다. --list로 확인하세요.")
        if args.list or spec is None:
            for number, probe in enumerate(probes, 1):
                print(f"{number:3}. {probe}")
        if args.list:
            return 0
        if spec is None:
            if not sys.stdin.isatty():
                parser.error("비대화형 실행에는 --probe-spec을 지정하세요.")
            choice = input("실행할 프로브 번호 (종료: q): ").strip()
            if choice.lower() == "q":
                return 0
            if not choice.isdigit() or not 1 <= int(choice) <= len(probes):
                parser.error("목록의 유효한 번호를 선택하세요.")
            spec = "probes." + probes[int(choice) - 1]
            probes = [probes[int(choice) - 1]]
        config = args.config.resolve()
        if not config.is_file():
            parser.error(f"설정 파일이 없습니다: {config}")
        prefix = "qwen-" + spec.removeprefix("probes.").replace(".", "-")
        prefix += "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        command = [sys.executable, "-m", "garak", "--config", str(config),
                   "--spec", spec, "--report_prefix", prefix]
        print(f"선택된 프로브 클래스: {len(probes)}개 (프롬프트 개수 아님)")
        print(shlex.join(command), flush=True)
        if args.dry_run:
            return 0
        # 기존 환경 값은 보존한다. 기본값은 인증 없는 로컬 서버용 공개 더미다.
        env = os.environ.copy()
        env.setdefault("OPENAICOMPATIBLE_API_KEY", "local-no-auth")
        print("보고서는 garak이 출력하는 경로에서 텍스트로 확인하세요.", flush=True)
        return subprocess.run(command, env=env).returncode
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
