import sys, time
from pathlib import Path
from typing import Optional

import typer
import yaml

from loguru import logger

from cryometrics import bluefors
from cryometrics.oxford import OxfordLog
from cryometrics.metric import Metric

logger.remove()
logger.add(sys.stderr)

### Bluefors Subprogram ###

bf_app = typer.Typer(no_args_is_help=True)

@bf_app.callback()
def main():
    ...

@bf_app.command()
def watch(
    ctx: typer.Context,
):
    while True:
        for line in sys.stdin:
            metric = Metric.from_line(line.rstrip())
            if metric.tags.get('metric_type') == 'pressure':
                new_metrics = bluefors.parse_pressure(metric)
            elif metric.tags.get('metric_type') == 'status':
                new_metrics = bluefors.parse_status(metric)
            else:
                new_metrics = [metric]

            for m in new_metrics:
                print(m.to_line())

            sys.stdout.flush()

        sys.stdout.flush()

### Oxford Subprogram ###

ox_app = typer.Typer(no_args_is_help=True)

@ox_app.callback()
def main():
    ...

@ox_app.command()
def watch(
    ctx: typer.Context,
    path: Path,
    config: Path = None,
    fridge: str = None,
    timestamp_col: str = None,
    start: Optional[int] = None,
):  
    if config is None:
        typer.echo(ctx.get_help())
        typer.echo('\nError: \'--config\' is required for influx format.')
        raise typer.Exit(code=1)
    
    with open(config, 'r') as f:
        config = yaml.load(f, Loader=yaml.CSafeLoader)
    
    if fridge:
        config.update(fridge=fridge)
    if timestamp_col:
        config.update(timestamp_col=timestamp_col)

    if path.is_file():
        log = OxfordLog.from_file(path)
    else:
        path = find_last_file(path)
        log = OxfordLog.from_file(path)

    logger.info(f'Watching log file: {path}')

    
    log.to_influx(None, start=start, **config)

    while True:
        log.to_influx(None, **config)
        time.sleep(5)

@ox_app.command()
def columns(file: Path):
    
    log = OxfordLog.from_file(file)

    typer.echo(f'Columns for file {file}:')
    for col in log.metadata.columns:
        typer.echo(col)

@ox_app.command()
def convert(
    ctx: typer.Context,
    file: Path,
    out: Path = None,
    fmt: str = 'csv',
    fridge: str = None,
    timestamp_col: str = None,
    start: Optional[int] = None,
    stop: Optional[int] = None,
    config: Optional[Path] = None,
):
    log = OxfordLog.from_file(file)

    if fmt == 'csv':
        log.to_csv(out, start, stop)
    elif fmt == 'influx':
        if config is None:
            typer.echo(ctx.get_help())
            typer.echo('\nError: \'--config\' is required for influx format.')
            raise typer.Exit(code=1)
        
        with open(config, 'r') as f:
            config = yaml.load(f, Loader=yaml.CSafeLoader)
        
        if fridge:
            config.update(fridge=fridge)
        if timestamp_col:
            config.update(timestamp_col=timestamp_col)

        log.to_influx(out, start=start, stop=stop, **config)

### Main Program ###

app = typer.Typer(no_args_is_help=True)
app.add_typer(bf_app, name="bluefors")
app.add_typer(ox_app, name="oxford")

@app.callback()
def main():
    ...


def find_last_file(directory: Path) -> Path:
    file = None

    last_mtime = 0
    for f in directory.iterdir():
        logger.debug(f'Getting mtime for file {f}.')
        mtime = f.stat().st_mtime
        if mtime >= last_mtime:
            last_mtime = mtime
            file = f

    return file

def main():
    app()

if __name__ == '__main__':
    main()