import logging
import os
import subprocess

log = logging.getLogger(__name__)


def run_command(command: str, **environment):
    """
    Execute the command, and log the result.

    Any additional keyword arguments passed into this call
    will be added as environment variables.
    """
    env = os.environ.copy()
    env.update(environment)
    result = subprocess.run(
        [command],
        shell=True,
        capture_output=True,
        env=env,
    )

    # Log and return output
    output = result.stderr.decode("utf-8").strip()
    log.info(output)
    return output
