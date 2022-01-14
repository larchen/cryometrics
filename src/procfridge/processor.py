import sys, time

from procfridge.metric import Metric
from procfridge.bluefors import parse_pressure, parse_status

def main():
    for line in sys.stdin:
        metric = Metric.from_line(line.rstrip())
        if metric.tags.get('metric_type') == 'pressure':
            new_metrics = parse_pressure(metric)
        elif metric.tags.get('metric_type') == 'status':
            new_metrics = parse_status(metric)
        else:
            new_metrics = [metric]

        for m in new_metrics:
            print(m.to_line())

        sys.stdout.flush()

    sys.stdout.flush()

if __name__ == '__main__':
    while True:
        main()

    '''
        >>> 143532 * 51
        7320132
        >>> 7309003 / 51
        143313.78431372548
        >>> 843942 / 6
        140657.0
        >>> quit()
    '''