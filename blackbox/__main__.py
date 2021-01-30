from sys import exit

from blackbox.cli import cli

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        exit()
