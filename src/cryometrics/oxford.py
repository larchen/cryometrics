import re, sys
from typing import Optional
from functools import reduce

import numpy as np

from attr import define, field

from cryometrics.metric import Metric

def split_blocks(bs: bytes, block_sizes: tuple[int, ...]) -> tuple[bytes, ...]:
    cum_sizes = np.cumsum((0, *block_sizes))
    return tuple(bs[cum_sizes[i]:cum_sizes[i+1]] for i in range(len(block_sizes)))

def parse_block(bs: bytes) -> list[str]:
    return tuple(s.decode('utf-8') for s in re.split(b'\x00+', bs) if s)

def default_blocks() -> dict[str, int]:
    """Returns a mapping of default block sizes."""
    return dict(header=1024, comments=5120, columns=5120, unknown=1024)

@define
class OxfordMetadata:
    header: str
    comments: str
    columns: tuple[str, ...]
    unknown: Optional[str] = None

    @classmethod
    def from_bytes(cls, bs: bytes, blocks: dict[str, int]) -> 'OxfordMetadata':
        metadata = dict()

        sizes = tuple(blocks.values())
        blockdata = split_blocks(bs, sizes)
        
        for bname, bdata in zip(blocks, blockdata):
            try:
                metadata[bname] = parse_block(bdata)
                if len(metadata[bname]) == 1:
                    metadata[bname] = metadata[bname][0]
            except UnicodeDecodeError:
                pass

        return cls(**metadata)

@define
class OxfordLog:
    filename: str
    blocks: dict[str, int] = field(factory=default_blocks)
    metadata: OxfordMetadata = None
    start: int = 0
    filepos: int = 0

    @classmethod
    def from_file(cls, filename: str, blocks: Optional[dict[str, int]] = None) -> 'OxfordLog':
        """Creates an OxfordLog object representing a given log file."""
        log = cls(filename=filename)
        
        if blocks:
            log.blocks = blocks

        metadata_bytes = sum(log.blocks.values())

        with open(filename, 'rb') as f:
            bin_data = f.read(metadata_bytes)
            fpos = f.tell()

        log.metadata = OxfordMetadata.from_bytes(bin_data, log.blocks)
        log.start = fpos
        log.filepos = fpos

        return log
        
    def read_lines(self, start=None, stop=None) -> np.ndarray:
        """Reads the specified log lines from the file."""
        if start is None:
            start = (self.filepos - self.start) // (len(self.metadata.columns) * 8)

        with open(self.filename, 'rb') as f:
            startpos = self.get_filepos(start)
            f.seek(startpos, 0 if startpos >= 0 else 2)
            datablock = f.read()

        data = np.frombuffer(datablock, float).reshape((-1, len(self.metadata.columns)))

        if stop and stop < start:
            raise ValueError(f'stop={stop} is less than start={start}' )
        elif stop:
            data = data[:stop - start, :]

        if data.size:
            self.filepos = int(self.get_filepos(data[-1, 1] + 1))

        return data

    def reset(self, line=0) -> int:
        """Resets the current file position."""
        self.filepos = self.get_filepos(line)
        return self.filepos

    def get_filepos(self, line=None) -> int:
        """Returns the file position that corresponds to the beginning of a line."""
        if line is None:
            return self.filepos

        bytes_per_line = len(self.metadata.columns) * 8 # Each column is 8 bytes
        filepos = line * bytes_per_line
        if filepos >= 0:
            filepos += self.start
        
        return filepos

    def to_csv(
        self,
        outfile: str,
        start: Optional[int] = None,
        stop: Optional[int] = None
    ) -> None:
        data = self.read_lines(start, stop)

        def is_int(col):
            return reduce(
                lambda b, x: (x in col.lower()) or b,
                ('line', 'time', 't(s)'),
                False
            )

        if outfile is None:
            outfile = sys.stdout.buffer

        np.savetxt(
            outfile,
            data,
            delimiter=',',
            fmt=[
                '%d' if is_int(col) else '%.4e' for col in self.metadata.columns
            ],
            header=self.metadata.header + '\n' + ','.join(self.metadata.columns)
        )

    def to_metrics(
        self,
        data: np.ndarray,
        fridge: str,
        metrics: dict,
        timestamp_col: str = 'Time(secs)'
    ) -> list[Metric]:
        out = []

        for line in data:
            datapoint = dict(zip(self.metadata.columns, line))

            timestamp = datapoint[timestamp_col]

            for col, metric_data in metrics.items():
                scaling = float(metric_data.pop('scaling', 1))

                m = Metric(
                    measurement=fridge,
                    tags=metric_data.get('tags', {}),
                    fields={metric_data['field']: datapoint[col]*scaling},
                    timestamp=int(timestamp*1e9)
                )

                out.append(m)

        return out

    def to_influx(
        self,
        outfile: str,
        fridge: str,
        metrics: dict,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        timestamp_col: str = 'Time(secs)',
    ) -> None:
        data = self.read_lines(start, stop)
        mlist = self.to_metrics(data, fridge, metrics, timestamp_col=timestamp_col)

        if outfile is None:
            sys.stdout.writelines(m.to_line(end='\n') for m in mlist)
            sys.stdout.flush()
        else:
            with open(outfile, 'a') as f:
                f.writelines(m.to_line(end='\n') for m in mlist)

# def watch_file(logfile: OxfordLog, )