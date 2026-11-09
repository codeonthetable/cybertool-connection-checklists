#!/usr/bin/env python3
"""Disposable MySQL/MariaDB connection lab. Python 3 and Docker; no host ports.

Prints only version/digest and checked outcomes, never generated credentials.
Pull the selected official image first. Defaults to the original MariaDB lab.
"""
import argparse
import datetime
import json
import re
import secrets
import subprocess
import time
import uuid

ENGINES = {
    'mariadb': {'image': 'mariadb:11.4', 'client': 'mariadb', 'memory': '512m',
                'tmpfs': '256m', 'refused_code': '2002',
                'env': 'MARIADB_ROOT_PASSWORD={password}\nMARIADB_INITDB_SKIP_TZINFO=1\n'},
    'mysql': {'image': 'mysql:8.4', 'client': 'mysql', 'memory': '1g',
              'tmpfs': '512m', 'refused_code': '2003',
              'env': 'MYSQL_ROOT_PASSWORD={password}\nMYSQL_INITDB_SKIP_TZINFO=1\n'},
}


def run(args, stdin=None, timeout=30):
    return subprocess.run(['docker', *args], input=stdin, text=True,
                          capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=sorted(ENGINES), default='mariadb')
    args = parser.parse_args()
    engine = ENGINES[args.engine]
    image = run(['image', 'inspect', engine['image'], '--format', '{{json .RepoDigests}}'])
    if image.returncode:
        raise RuntimeError('First run: docker pull ' + engine['image'])
    digests = json.loads(image.stdout)
    name = 'cybertool-mysql-lab-' + uuid.uuid4().hex[:12]
    password = secrets.token_hex(24)
    started = False
    report = {'tested_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'engine': args.engine, 'image': engine['image'], 'image_digests': digests, 'network': 'none',
              'published_ports': [], 'cases': []}
    try:
        created = run(['run', '-d', '--name', name, '--network', 'none',
                       '--memory', engine['memory'], '--cpus', '1', '--pids-limit', '128',
                       '--tmpfs', '/var/lib/mysql:rw,size=' + engine['tmpfs'],
                       '--env-file', '/dev/stdin', engine['image']],
                      engine['env'].format(password=password))
        if created.returncode:
            raise RuntimeError('Disposable container could not start')
        started = True

        def client(options, secret=password):
            # Secret enters via stdin, not command arguments or saved files.
            return run(['exec', '-i', name, 'sh', '-c',
                        'MYSQL_PWD=$(cat); export MYSQL_PWD; exec "$@"',
                        'lab', engine['client'], '--connect-timeout=3', '--batch', '--skip-column-names',
                        '--user=root', *options, '-e', 'SELECT 1'], secret, 10)

        tcp = ['--protocol=TCP', '--host=127.0.0.1', '--port=3306']
        for _ in range(120):
            if client(tcp).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Isolated database did not become ready within 120 attempts')
        version = run(['exec', name, engine['client'], '--version'])
        if version.returncode:
            raise RuntimeError('Cannot read client version')
        report['client_version'] = version.stdout.strip()
        cases = [
            ('tcp_refused', ['--protocol=TCP', '--host=127.0.0.1', '--port=3307'], password, engine['refused_code']),
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
