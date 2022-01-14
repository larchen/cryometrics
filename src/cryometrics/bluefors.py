import re

from cryometrics.metric import Metric

SCI = r'((?:\+|-)?\d+.\d+E[+-]\d+)'
PRESSURE_REGEX = re.compile(rf'(CH\d).*?{SCI}')
STATUS_REGEX = re.compile(r'([^,]+?),((?:\+|-)?\d+.\d+E[+-]\d+)')
STATUS_ID_REGEX = re.compile(r'([a-zA-Z\d]+)_?(\d)?')

def parse_pressure(metric: Metric) -> list[Metric]:
    pstr = metric.fields['pressures']

    pressures = PRESSURE_REGEX.findall(pstr)

    metrics = []

    for ch, p in pressures:
        metrics.append(
            Metric(
                measurement=metric.measurement,
                tags=metric.tags.copy(),
                fields=dict(pressure=p),
                timestamp=metric.timestamp
            )
        )
        metrics[-1].tags.update(channel=ch)

    return metrics

def parse_status(metric: Metric) -> list[Metric]:
    statstr = metric.fields['status']

    statuses = STATUS_REGEX.findall(statstr)

    metrics = []

    for k, s in statuses:
        key, idx = STATUS_ID_REGEX.match(k).groups()
        idx = idx or 1

        metrics.append(
            Metric(
                measurement=f'{metric.measurement}',
                tags=metric.tags.copy(),
                fields={key: s},
                timestamp=metric.timestamp
            )
        )
        metrics[-1].tags.update({
            ('compressor' if key.startswith('c') else 'pump'): str(idx),
        })

    return metrics
