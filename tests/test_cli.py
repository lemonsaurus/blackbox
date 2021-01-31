from os import remove as delete_file
from tempfile import NamedTemporaryFile

from click.testing import CliRunner

from blackbox.__main__ import cli
from blackbox.__version__ import __version__


def test_cli_outputs_version_number():
    """
    Test CLI --version flag
    """

    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert result.output == f'{__version__}\n'


def test_cli_run(config_file, mocker):
    """
    Test CLI --version flag
    """
    # TODO: Find a way to mock the database.backup() and other calls that are wrapped in abstraction
    temp = NamedTemporaryFile("w", delete=False)
    temp.write(config_file)
    temp.close()

    runner = CliRunner()
    result = runner.invoke(cli, ['--config', temp.name])

    # Cleanup
    delete_file(temp.name)

    assert result.exit_code == 0
