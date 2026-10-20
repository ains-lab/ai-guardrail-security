"""codex-lb OpenAI 호환 API를 대상으로 garak encoding 검사.

CODEX_LB_BASE_URL과 CODEX_LB_API_KEY를 환경 변수에 설정한다.
기본 모델은 원본 YAML의 model_name이며 --model로 명시적으로 바꿀 수 있다.
--dry-run/--list는 API 키 없이 동작하고 모델 요청을 보내지 않는다.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

import yaml

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HERE / 'probe-encoding-openai.yaml')
    parser.add_argument('--base-url', default=os.getenv('CODEX_LB_BASE_URL'))
    parser.add_argument('--model', default=os.getenv('CODEX_LB_MODEL'))
    parser.add_argument('--probe-spec', help='encoding 또는 encoding.InjectBase64 등')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--allow-approved-http', action='store_true',
                        help='사용자가 승인한 10.10.1.244:2455 사설망 HTTP에만 키 전송 허용')
    parser.add_argument('--prompt-cap', type=int, help='초기 검증용 프로브 프롬프트 soft cap')
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        parser.error('YAML 최상위는 객체여야 합니다.')
    plugins = config.setdefault('plugins', {})
    spec = args.probe_spec or plugins.get('probe_spec', 'encoding')
    spec = spec.removeprefix('probes.')
    if not re.fullmatch(r'encoding(?:\.[A-Za-z_][A-Za-z_0-9]*)?', spec):
        parser.error('encoding 계열의 모듈 또는 클래스만 지정하세요.')
    selected = 'probes.' + spec
    listing = subprocess.run([sys.executable, '-m', 'garak', '--list_probes', '--spec', selected],
                             capture_output=True, text=True, check=True)
    output = re.sub(r'\x1b\[[0-9;]*m', '', listing.stdout)
    names = re.findall(r'^probes:\s+(encoding\.[A-Za-z_0-9]+)', output, re.MULTILINE)
    if not names:
        parser.error('설치된 프로브가 없습니다.')
    if args.list:
        print('\n'.join(names))
        return
    if not args.base_url:
        parser.error('CODEX_LB_BASE_URL 또는 --base-url을 지정하세요. 키는 URL에 넣지 마세요.')
    url = urlsplit(args.base_url)
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error('자격증명·쿼리 없는 http(s) API 기본 주소가 필요합니다.')
    if url.scheme == 'http' and url.hostname not in ('localhost', '127.0.0.1', '::1'):
        if not (args.allow_approved_http and url.netloc == '10.10.1.244:2455' and url.path.rstrip('/') == '/v1'):
            parser.error('원격 endpoint는 HTTPS가 필요합니다. 승인된 사설망 주소만 --allow-approved-http로 허용합니다.')
    if args.prompt_cap is not None:
        if args.prompt_cap < 1:
            parser.error('--prompt-cap은 양수여야 합니다.')
        config.setdefault('run', {})['soft_probe_prompt_cap'] = args.prompt_cap
    model = args.model or plugins.get('target_name') or plugins.get('model_name')
    if not model:
        parser.error('모델을 지정하세요.')
    # 레거시 선택은 명시적인 --spec으로 전달. 원본 YAML은 수정하지 않는다.
    for key in ('probe_spec', 'model_type', 'model_name'):
        plugins.pop(key, None)
    plugins['target_type'] = 'openai.OpenAICompatible'
    plugins['target_name'] = model
    plugins['generators'] = {'openai': {'OpenAICompatible': {
        'uri': args.base_url.rstrip('/') + '/', 'temperature': 0.0,
        'max_tokens': 256,
        'suppressed_params': ['stop', 'presence_penalty', 'frequency_penalty', 'temperature', 'top_p', 'seed', 'n'],
    }}}
    config.setdefault('system', {}).update(parallel_requests=1, parallel_attempts=1)
    # 보고서 디렉터리는 명시적으로 이 실습의 reports/codex-lb 아래에 고정한다.
    report_dir = HERE / 'reports/codex-lb'
    config.setdefault('reporting', {})['report_dir'] = str(report_dir)
    prefix = 'codex-lb-' + spec.replace('.', '-') + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    print(json.dumps({'endpoint': args.base_url, 'model': model, 'spec': selected,
                      'probe_classes': len(names), 'report_dir': str(report_dir)}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    key = os.getenv('CODEX_LB_API_KEY')
    if not key:
        parser.error('CODEX_LB_API_KEY 환경 변수가 필요합니다.')
    env = os.environ.copy()
    env['OPENAICOMPATIBLE_API_KEY'] = key
    # 임시 설정에는 키를 넣지 않는다. 가급적 보고서/로그에도 키를 쓰지 않는다.
    with tempfile.TemporaryDirectory(prefix='garak-codex-lb-') as directory:
        path = Path(directory) / 'config.yaml'
        path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding='utf-8')
        return subprocess.run([sys.executable, '-m', 'garak', '--config', str(path),
                               '--spec', selected, '--report_prefix', prefix], env=env).returncode


if __name__ == '__main__':
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(130)
