import os
import subprocess
import logging

log = logging.getLogger(__name__)


def run_command(command: str, cwd: bool = None):
    """Execute the command, and log the result."""
    env = os.environ.copy()
    result = subprocess.run(
        [command],
        shell=True,
        capture_output=True,
        cwd=cwd,
        env=env,
    )

    # Log and return output
    output = result.stderr.decode("utf-8").strip()
    log.info(output)
    return output
