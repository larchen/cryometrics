import re, shlex

from typing import Any, Union, TypeVar
from attr import define, field

FieldValue = TypeVar('FieldValue', str, float, int, bool)

FIELD_REGEX = re.compile(r'(?:(?:[^,]|\\,)*)=(?:\".*?(?<!\\)\"|[^,]*)')

def parse_field(field_str: str) -> FieldValue:
    if '\"' in field_str:
        return field_str.strip('"')

    if field_str in ('t', 'T', 'true', 'True', 'TRUE'):
        return True
    
    if field_str in ('f', 'F', 'false', 'False', 'FALSE'):
        return False

    if field_str.endswith('i'):
        return int(field_str.strip('i'))
    
    return float(field_str)

@define
class Metric:
    measurement: str
    tags: dict[str, str] = field(factory=dict)
    fields: dict[str, FieldValue] = field(factory=dict)
    timestamp: int = None

    @classmethod
    def from_line(cls, line: str) -> 'Metric':
        def esplit(delim, val, **kwargs):
            return re.split(rf'(?<!\\){delim}', val, **kwargs)

        def remove_escape(k, v, escape='\\'):
            return k.replace(escape, ''), v.replace(escape, '')

        # split measurement + tags based on whitespace 1
        meas_tags, rest = esplit(' ', line, maxsplit=1)
        meas_tags = esplit(',', meas_tags, maxsplit=1)

        if len(meas_tags) == 1:
            measurement = meas_tags[0]
        elif len(meas_tags) == 2:
            measurement, tags = meas_tags
        else:
            raise ValueError(f'Invalid influx line: {line}')

        try:
            fields, maybe_timestamp = rest.rsplit(' ', maxsplit=1)
            timestamp = int(maybe_timestamp)
        except ValueError:
            fields = rest
            timestamp = None

        tagdict = dict(remove_escape(*esplit('=', t)) for t in esplit(',', tags))
        fielddict = dict(
            remove_escape(*esplit('=', f)) for f in FIELD_REGEX.findall(fields)
        )

        for key in fielddict:
            fielddict[key] = parse_field(fielddict[key])

        return cls(
            measurement=measurement,
            tags=tagdict,
            fields=fielddict,
            timestamp=timestamp
        )

    def to_line(self, end='') -> str:
        def escape(s: str, esc: str = ' ,='):
            for c in esc:
                s = s.replace(c, f'\\{c}')
            return s

        def format_field(v: FieldValue):
            if isinstance(v, float) and v.is_integer():
                v = int(v)

            return str(v)

        esc_meas = escape(self.measurement, ' ,')
        esc_tags = ','.join(f'{escape(k)}={escape(v)}' for k, v in self.tags.items())
        esc_fields = ','.join(f'{escape(k)}={format_field(v)}' for k, v in self.fields.items())
        timestamp = f' {self.timestamp}' if self.timestamp else ''

        if esc_tags:
            esc_tags = ',' + esc_tags

        return f'{esc_meas}{esc_tags} {esc_fields}{timestamp}{end}'