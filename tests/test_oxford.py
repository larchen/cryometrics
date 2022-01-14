from pathlib import Path

import pytest

from procfridge.oxford import OxfordLog

LOGDIR = Path(__file__).parent / 'logs'

class TestLog:
    def test_from_file(self):
        log = OxfordLog.from_file(filename='F:\\Fridges\\Oxicold\\log 220110 170517.vcl')
        
        assert isinstance(log, OxfordLog)

    @pytest.mark.parametrize('line,filepos', [
        (0, 12288),
        (None, 12288),
        (1, 12800),
        (-10, -5120),
    ])
    def test_get_filepos(self, line, filepos):
        logdir = LOGDIR / 'oxicold'
        filename = next(logdir.iterdir())

        log = OxfordLog.from_file(filename=filename)

        assert log.get_filepos(line) == filepos

    @pytest.mark.parametrize('start,stop,lines', [
        (0, 5, (0, 4)),
        (None, 403, (0, 402)),
        (None, 410, (0, 403)),
        (None, None, (0, 403)),
        (-10, None, (394, 403)),
        (-1, None, (403, 403))
    ])
    def test_read_line(self, start, stop, lines):
        logdir = LOGDIR / 'oxicold'
        filename = next(logdir.iterdir())

        log = OxfordLog.from_file(filename=filename)
    
        first, last = log.read_lines(start, stop)[:, 1].astype(int)[[0, -1]]

        assert (first, last) == lines

    def test_current_filepos(self):
        logdir = LOGDIR / 'oxicold'
        filename = next(logdir.iterdir())

        log = OxfordLog.from_file(filename=filename)

        first, last = log.read_lines(stop=10)[:, 1].astype(int)[[0, -1]]
        assert (first, last) == (0, 9)
        first, last = log.read_lines(stop=20)[:, 1].astype(int)[[0, -1]]
        assert (first, last) == (10, 19)
