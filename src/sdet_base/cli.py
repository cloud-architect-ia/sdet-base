import click
from .core.processor import run

@click.command()
@click.option("--input", required=True)
def main(input: str):
    run(input)

if __name__ == "__main__":
    main()
