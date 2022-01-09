import os
from collections import Counter
from dataclasses import dataclass

import click
import pandas as pd

from handler import TanglinTennisCourtHandler


@click.command()
@click.option('-u', '--username', default=os.getenv('UID'), help="Login ID")
@click.option('-p', '--password', default=os.getenv('PWD'), help="Password")
@click.option('--indoor/--outdoor', default=True, help="If set, books indoor courts. Can also use --outdoors to specify outdoor courts. Defaults to indoors")
@click.option('--duration', default=2, type=int, help="Number of hours to reserve. Defaults to 2.")
@click.option('--date', type=str, help="Date to make reservation. See README for more info on how the default works")
@click.option('-t', '--times', multiple=True, type=int, default=[7, 8],
              help="A list of times to book. Defaults to 7 and 8 am. Must not have duplicates. Times are reserved in order of priority. "
                   "So if you like a 9am slot over an 8am one, put -t 9 -t 8")
def book_tanglin_tennis_courts(username: str,
                               password: str,
                               indoor: bool,
                               duration: int,
                               date: str,
                               times: list[int]):
    """
    Command line function to make reservation for the Tanglin Club Tennis courts
    """
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
            now = pd.Timestamp.now()
            if now > now.floor('d').replace(hour=7):
                now = now.ceil('d')  # move to next day
            else:
                now = now.floor('d')  # drop to current day

            return (now + pd.offsets.Day(7)).strftime('%Y-%m-%d')
        else:
            try:
                return pd.Timestamp(date).strftime('%Y-%m-%d')
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
        if len(times) != len(set(times)):
            duplicates = [x for x, c in Counter(times).items() if c > 1]
            raise ValueError(f"The following times are duplicated: {sorted(duplicates)}")

        for t in times:
            assert isinstance(t, int) and 6 <= t <= 22, "time must be between 6 to 22 (hours, 6am to 10pm)"

        return times


if __name__ == '__main__':
    book_tanglin_tennis_courts()
