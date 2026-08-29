import os
import time
import tempfile
import subprocess
from django.conf import settings
import requests

LANG_IMAGE_MAP = {
    'c': ('gcc:13.2', 'gcc /code/main.c -o /code/main && /code/main'),
    'cpp': ('gcc:13.2', 'g++ -std=c++17 /code/main.cpp -o /code/main && /code/main'),
    'java': ('eclipse-temurin:21-jdk-jammy', 'javac /code/Main.java -d /code && java -cp /code Main'),
    'python': ('python:3.11-slim', 'python3 /code/main.py'),
    'python3': ('python:3.11-slim', 'python3 /code/main.py'),
    'go': ('golang:1.22', 'cd /code && go run main.go'),
    'javascript': ('node:20-alpine', 'node /code/main.js'),
    'typescript': ('node:20-alpine', 'npx --yes tsx /code/main.ts'),
    'kotlin': ('azul/zulu-openjdk:21', 'kotlinc /code/main.kt -include-runtime -d /code/main.jar && java -jar /code/main.jar'),
    'rust': ('rust:1.77', 'cd /code && rustc main.rs -o main && ./main'),
    'csharp': ('mcr.microsoft.com/dotnet/sdk:8.0', 'cd /code && dotnet-script main.csx'),
}

LANG_EXTENSION = {
    'c': 'c', 'cpp': 'cpp', 'java': 'java', 'python': 'py', 'python3': 'py',
    'go': 'go', 'javascript': 'js', 'typescript': 'ts',
    'kotlin': 'kt', 'rust': 'rs', 'csharp': 'csx',
}

def judge_via_service(language, code, test_cases, time_limit_ms, memory_limit_mb):
    payload = {
        "language": language,
        "code": code,
        "test_cases": [
            {"input": tc['input'], "output": tc['expected_output']}
            for tc in test_cases
        ],
        "time_limit_ms": int(time_limit_ms),
        "memory_limit_mb": int(memory_limit_mb),
    }
    try:
        resp = requests.post(
            settings.JUDGE_SERVICE_URL,
            json=payload,
            timeout=max(30, len(test_cases) * 30 + 10),
        )
        if resp.status_code != 200:
            return None, f"judge service http {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        return data, None
    except requests.RequestException as e:
        return None, f"judge service unreachable: {str(e)[:200]}"

def _normalize_output(s):
    return (s or "").replace("\r\n", "\n").rstrip()

def _run_single_case_local(language, code, input_data, time_limit_ms, memory_limit_mb):
    if language not in LANG_IMAGE_MAP:
        return {'status': 'Internal Error', 'stdout': '', 'stderr': f'unsupported: {language}',
                'returncode': -1, 'time_ms': 0, 'wall_time_ms': 0}

    image, command = LANG_IMAGE_MAP[language]
    ext = LANG_EXTENSION.get(language, 'txt')
    filename = f'main.{ext}'

    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, filename)
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)

        start = time.perf_counter()
        try:
            completed = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '--network', 'none',
                    '--pids-limit', '256',
                    '--read-only',
                    '--tmpfs', '/tmp:rw,size=64m',
                    f'--memory={memory_limit_mb}m',
                    f'--cpus=0.5',
                    '-v', f'{tmpdir}:/code:ro',
                    '--entrypoint', 'sh',
                    image,
                    '-c', f"timeout {max(1, time_limit_ms / 1000):.3f} {command}"
                ],
                input=input_data or '',
                capture_output=True,
                text=True,
                timeout=max(60, time_limit_ms * len(input_data or '') / 1000 + 10),
            )
            wall_ms = (time.perf_counter() - start) * 1000
            rc = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        
            if rc == 124:
                status = 'Time Limit Exceeded'
            elif rc != 0:
                if stderr and any(kw in stderr.lower() for kw in ['compile', 'error', 'syntax']):
                    status = 'Compile Error'
                else:
                    status = 'Runtime Error'
            else:
                status = 'Running'
            return {
                'status': status,
                'stdout': stdout,
                'stderr': stderr,
                'returncode': rc,
                'time_ms': wall_ms,
                'wall_time_ms': wall_ms,
            }
        except subprocess.TimeoutExpired:
            return {'status': 'Time Limit Exceeded', 'stdout': '', 'stderr': 'timeout',
                    'returncode': 124,
                    'time_ms': time_limit_ms, 'wall_time_ms': time_limit_ms}
        except Exception as e:
            return {'status': 'Internal Error', 'stdout': '', 'stderr': str(e),
                    'returncode': -1, 'time_ms': 0, 'wall_time_ms': 0}

def run_judge_local(language, code, test_cases, time_limit_ms, memory_limit_mb):
    results = []
    passed = 0
    total = len(test_cases)
    for i, tc in enumerate(test_cases, 1):
        r = _run_single_case_local(language, code, tc.get('input', ''), time_limit_ms, memory_limit_mb)
        r['case'] = i
        if r['status'] == 'Running':
            if _normalize_output(r.get('stdout', '')) == _normalize_output(tc.get('expected_output', '')):
                r['status'] = 'Accepted'
                passed += 1
            else:
                r['status'] = 'Wrong Answer'
        results.append(r)

    overall = 'Accepted' if passed == total and total > 0 else (
        results[0]['status'] if results else 'Internal Error'
    )
    for r in results:
        if r['status'] != 'Accepted':
            overall = r['status']
            break
    return {
        'status': overall,
        'passed': passed,
        'total': total,
        'results': results,
    }

def judge_all(language, code, test_cases, time_limit_ms, memory_limit_mb):
    if memory_limit_mb < 16:
        memory_limit_mb = 16
    if memory_limit_mb > 2048:
        memory_limit_mb = 2048
    if time_limit_ms <= 0:
        time_limit_ms = settings.JUDGE_DEFAULT_TIME_LIMIT_MS

    data, err = judge_via_service(language, code, test_cases, time_limit_ms, memory_limit_mb)
    if data is not None:
        return data
    if getattr(settings, 'JUDGE_FALLBACK_LOCAL', True):
        return run_judge_local(language, code, test_cases, time_limit_ms, memory_limit_mb)
    return {'status': 'Internal Error', 'passed': 0, 'total': len(test_cases),
            'results': [{'status': 'Internal Error', 'time_ms': 0, 'stdout': '',
                         'stderr': err or '', 'returncode': -1,
                         'wall_time_ms': 0, 'case': i + 1}
                        for i in range(len(test_cases))]}
