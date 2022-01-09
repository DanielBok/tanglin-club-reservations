Tennis Reservations
===================

## Getting Started

To get started, you need to have installed

1. Python >= 3.10
2. Pipenv
    1. This is done after installing Python
    2. In the terminal, execute `pip install pipenv`
3. Go into the folder where you've cloned this project (in the terminal)
4. Install the required packages via Pipenv
    1. In the terminal, execute `pipenv sync`

## Day to day ops

If the `date` flag is not manually specified, the default booking date will be 1 week ahead. If the time is 2022-01-03
06:00, then the default date is 2022-01-10. However, if it is past 7am (i.e. 2022-01-03 07:10), then the default date is
2022-01-11. This is because we assume that the other members will have already snapped up all the slots.

To execute the script in the command shell:

```shell
# see command line docs 
python terminal.py --help

# Books indoor courts
# Prefer 8am then 7 am then 10am. 
# books for duration of 2 hours
# uses default date
# Note that it only books one court, if one is successful, program halts
python terminal.py -u loginId -p loginPwd --indoor -t 8 -t 7 -t 10 -duration 2
```
