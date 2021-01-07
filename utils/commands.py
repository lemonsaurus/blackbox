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
    # Get the current environment variables.
    env = os.environ.copy()

    # Now add all the environment variables we passed in that are not None.
    extra_env = {key: value for key, value in environment.items() if value is not None}
    env.update(extra_env)

    # Run the command and capture the output
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
