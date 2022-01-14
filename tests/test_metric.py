import pytest

from procfridge.metric import Metric

class TestMetric:
    CASES = [
        (
            'weather,location=us-midwest,season=summer temperature=82 1465839830100400200',
            Metric(measurement='weather', tags=dict(location='us-midwest', season='summer'), fields=dict(temperature=82.0), timestamp=1465839830100400200)
        ),
        (
            r'weather,location\ place=us-midwest temperature=82 1465839830100400200',
            Metric(measurement='weather', tags={'location place': 'us-midwest'}, fields=dict(temperature=82.0), timestamp=1465839830100400200)
        )
    ]

    @pytest.mark.parametrize('line,metric', CASES)
    def test_parser(self, line, metric):
        parsed = Metric.from_line(line)

        assert parsed == metric

    @pytest.mark.parametrize('line,metric', CASES)
    def test_dumper(self, line, metric):
        dumped = metric.to_line()

        assert dumped == line