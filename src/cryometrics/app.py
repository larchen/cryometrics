import sys, time
from pathlib import Path
from typing import Optional

import typer
import yaml

from loguru import logger

from cryometrics import bluefors
from cryometrics.oxford import OxfordLog
from cryometrics.metric import Metric
from cryometrics.database import send_http_data

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
    start: Optional[int] = -1,
    sleep: int = 10
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
        time.sleep(sleep)

@ox_app.command()
def backfill(
    ctx: typer.Context,
    path: Path,
    config: Path = None,
    fridge: str = None,
    timestamp_col: str = None,
    start: Optional[int] = None,
    stop: Optional[int] = None,
    max_lines: int = 10000,
    endpoint: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    num_tries: int = 5,
    backoff: int = 1 
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
        typer.echo('Error: specified \'--path\' must be a log file, not a directory.')
        raise typer.Exit(code=1)

    if endpoint:
        success = send_http_data(
            endpoint, '', username=username, password=password
        )
        status = 'Successfully connected' if success else 'Failed to connect'
        logger.info(f'{status} to database at {endpoint}')

        if not success:
            raise typer.Exit(code=1)
    else:
        typer.echo('No endpoint specified, writing to stdout:')

    data = log.read_lines(start=start, stop=stop)

    typer.echo(f'Parsing metrics from {path}...')
    all_metrics = log.to_metrics(data, **config)

    with typer.progressbar(
        range(0, len(all_metrics), max_lines), label=f'Sending {len(all_metrics)} metrics'
    ) as progress:
        for idx in progress:
            to_send = '\n'.join(
                m.to_line() for m in all_metrics[idx:idx + max_lines]
            )
            if endpoint:
                for t in range(num_tries):
                    success = send_http_data(
                        endpoint,
                        to_send,
                        username=username,
                        password=password
                    )
                    if success:
                        break
                    time.sleep(backoff ** t)
                else:
                    typer.echo('Failed to send data!')
                    raise typer.Exit(code=1)
            else:
                typer.echo(to_send)

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