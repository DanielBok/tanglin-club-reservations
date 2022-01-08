import os
from dataclasses import dataclass
from datetime import datetime, timedelta

import click

from handler import TanglinTennisCourtHandler


@click.command()
@click.option('-u', '--username', default=os.getenv('UID'))
@click.option('-p', '--password', default=os.getenv('PWD'))
@click.option('--indoor/--outdoor', default=True)
@click.option('--duration', default=2, type=int)
@click.option('--date', type=str)
@click.option('-t', '--times', multiple=True, type=int, default=[8])
def book_tanglin_tennis_courts(username: str,
                               password: str,
                               indoor: bool,
                               duration: int,
                               date: str,
                               times: list[int]):
    args = Arguments(username, password, indoor, duration, date, times)
    _run_handler(args)


def _run_handler(args: 'Arguments'):
    handler = TanglinTennisCourtHandler(args.username, args.password)
    handler.make_reservations(args.date, args.indoor, args.duration, args.times)


@dataclass
class Arguments:
    username: str
    password: str
    indoor: bool
    duration: int
    date: str
    times: list[int]

    def __post_init__(self):
        self.username = self._validate_non_empty_string('username', self.username)
        self.password = self._validate_non_empty_string('password', self.password)
        self.date = self._validate_date(self.date)

        assert self.duration in (1, 2), "duration can only be 1 or 2 hours"
        self.times = self._validate_times(self.times)

    @staticmethod
    def _validate_date(date: str):
        if date is None:
            return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        else:
            try:
                return datetime.strptime(date, "%Y-%m-%d").strftime('%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Invalid date: '{date}'. Please use format YYYY-MM-DD")

    @staticmethod
    def _validate_non_empty_string(field: str, value: str):
        value = value.strip()
        assert len(value) > 0, f"{field} must be provided and must not be an empty string"
        return value

    @staticmethod
    def _validate_times(times: list[int]):
        assert len(times) > 0, "times must be provided"
        for t in times:
            assert isinstance(t, int) and 6 <= t <= 22, "time must be between 6 to 22 (hours, 6am to 10pm)"

        return sorted(set(times))


if __name__ == '__main__':
    book_tanglin_tennis_courts()
