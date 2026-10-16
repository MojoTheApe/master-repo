#!/usr/bin/env python3
"""Compare fresh source+main with fresh source+verified-reuse commands locally.

Commands are JSON argv arrays, never shell text. The reuse command must establish
actual supported proof; this harness measures it, not its correctness. Native
job billing/network and fleet savings are deliberately not inferred.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
import time


def argv(value):
    result = json.loads(value)
    if not isinstance(result, list) or not result or any(not isinstance(x, str) or not x for x in result):
        raise argparse.ArgumentTypeError('Supply a nonempty JSON argv array')
    return result


def measure(fresh, reuse, repetitions=3, timeout=300):
    if os.name != 'posix':
        raise RuntimeError('This local harness requires POSIX process-group cleanup; use native job metrics on other hosts')
    rows = []
    for iteration in range(repetitions):
        # Alternate order to expose warming/order effects instead of always
        # charging cold initialization to the unoptimized baseline.
        routes = ('fresh', 'reuse') if iteration % 2 == 0 else ('reuse', 'fresh')
        for route in routes:
            started = time.perf_counter(); steps = []
            for command in (fresh, fresh if route == 'fresh' else reuse):
                at = time.perf_counter()
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                try:
                    process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    process.communicate()
                    raise RuntimeError('A measurement command timed out; its process group was stopped') from None
                if process.returncode:
                    raise RuntimeError('A measurement command failed; no performance result is valid')
                steps.append(time.perf_counter()-at)
            rows.append({'iteration': iteration+1, 'route': route, 'first_feedback_seconds': steps[0],
                         'main_seconds': steps[1], 'cycle_seconds': time.perf_counter()-started,
                         'local_step_seconds': sum(steps)})
    medians = {route: {key: statistics.median(row[key] for row in rows if row['route']==route)
                       for key in ('first_feedback_seconds', 'main_seconds', 'cycle_seconds', 'local_step_seconds')}
               for route in ('fresh', 'reuse')}
    return {'schema_version': 1, 'measurement_kind': 'local-command-comparison', 'repetitions': repetitions,
            'rows': rows, 'medians': medians, 'native_job_seconds': None,
            'limits': 'Local commands only; not native billing, network latency, platform acceptance or fleet savings.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-command', type=argv, required=True)
    parser.add_argument('--reuse-command', type=argv, required=True)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 20 or not 1 <= args.timeout <= 3600:
        parser.error('Use 1..20 repetitions and a 1..3600 second command timeout')
    try:
        value = measure(args.fresh_command, args.reuse_command, args.repetitions, args.timeout)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, 'Measurement unavailable: '+str(error)+'\n')
    args.output.write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(value['medians'], indent=2))


if __name__ == '__main__':
    main()
