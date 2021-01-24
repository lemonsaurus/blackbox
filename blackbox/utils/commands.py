import os
import subprocess
from typing import Tuple

from blackbox.utils.logger import log


def run_command(command: str, **environment) -> Tuple[bool, str]:
    """
    Execute the command, and log the result.

    Any additional keyword arguments passed into this call
    will be added as environment variables.

    Returns a tuple of (success, output), where success is a boolean value
    that is either True or False, and output is a string.
    """
    # Get the current environment variables.
    env = os.environ.copy()

    # Now add all the environment variables we passed in that are not None.
    extra_env = {key: value for key, value in environment.items() if value is not None}
    env.update(extra_env)

    # Run the command and capture the output
    try:
        result = subprocess.run(
            [command],
            shell=True,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output = result.stdout.decode("utf-8").strip()
        success = True
    except subprocess.CalledProcessError as e:
        output = e.stdout.decode("utf-8").strip()
        success = False

    # Log and return output
    log.info(output)
    return success, output
