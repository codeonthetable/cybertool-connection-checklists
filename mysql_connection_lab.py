#!/usr/bin/env python3
"""Disposable MariaDB connection lab. Requires Python 3 and Docker; no host ports.

Prints only version/digest and checked outcomes, never generated credentials.
The Docker daemon must already have the official mariadb:11.4 image available.
"""
import datetime
import json
import re
import secrets
import subprocess
import time
import uuid

IMAGE = 'mariadb:11.4'


def run(args, stdin=None, timeout=30):
    return subprocess.run(['docker', *args], input=stdin, text=True,
                          capture_output=True, timeout=timeout)


def main():
    image = run(['image', 'inspect', IMAGE, '--format', '{{json .RepoDigests}}'])
    if image.returncode:
        raise RuntimeError('First run: docker pull mariadb:11.4')
    digests = json.loads(image.stdout)
    name = 'cybertool-mysql-lab-' + uuid.uuid4().hex[:12]
    password = secrets.token_hex(24)
    started = False
    report = {'tested_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'image': IMAGE, 'image_digests': digests, 'network': 'none',
              'published_ports': [], 'cases': []}
    try:
        created = run(['run', '-d', '--name', name, '--network', 'none',
                       '--memory', '512m', '--cpus', '1', '--pids-limit', '128',
                       '--tmpfs', '/var/lib/mysql:rw,size=256m',
                       '--env-file', '/dev/stdin', IMAGE],
                      'MARIADB_ROOT_PASSWORD=' + password + '\nMARIADB_INITDB_SKIP_TZINFO=1\n')
        if created.returncode:
            raise RuntimeError('Disposable container could not start')
        started = True

        def client(options, secret=password):
            # Secret enters via stdin, not command arguments or saved files.
            return run(['exec', '-i', name, 'sh', '-c',
                        'MYSQL_PWD=$(cat); export MYSQL_PWD; exec mariadb "$@"',
                        'lab', '--connect-timeout=3', '--batch', '--skip-column-names',
                        '--user=root', *options, '-e', 'SELECT 1'], secret, 10)

        tcp = ['--protocol=TCP', '--host=127.0.0.1', '--port=3306']
        for _ in range(60):
            if client(tcp).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Isolated database did not become ready within 60 attempts')
        version = run(['exec', name, 'mariadb', '--version'])
        if version.returncode:
            raise RuntimeError('Cannot read client version')
        report['client_version'] = version.stdout.strip()
        cases = [
            ('tcp_refused', ['--protocol=TCP', '--host=127.0.0.1', '--port=3307'], password, '2002'),
            ('authentication_denied', tcp, secrets.token_hex(24), '1045'),
            ('missing_socket', ['--protocol=SOCKET', '--socket=/tmp/cybertool-absent.sock'], password, '2002'),
            ('authenticated_control', tcp, password, None),
        ]
        for label, options, secret, expected_code in cases:
            result = client(options, secret)
            match = re.search(r'ERROR (\d+) \(([A-Z0-9]+)\)', result.stderr)
            code = match.group(1) if match else None
            passed = (result.returncode != 0 and code == expected_code) if expected_code else (result.returncode == 0 and result.stdout.strip() == '1')
            report['cases'].append({'case': label, 'exit_code': result.returncode,
                                    'error_code': code, 'sqlstate': match.group(2) if match else None,
                                    'query_result': '1' if expected_code is None and passed else None,
                                    'passed': passed})
        if not all(case['passed'] for case in report['cases']):
            raise RuntimeError('Unexpected lab result; no successful verification claimed')
    finally:
        if started:
            cleaned = run(['rm', '-f', '-v', name])
            if cleaned.returncode:
                raise RuntimeError('Lab cleanup failed for ' + name)
    report['cleanup'] = 'completed'
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
