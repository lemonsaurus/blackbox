import tomlkit


def get_project_version():
    """Set version only in toml file and get it wherever you want."""
    with open('pyproject.toml') as pyproject:
        file_contents = pyproject.read()

    return tomlkit.parse(file_contents)['tool']['poetry']['version']


# If we call this file we return version for docker push action.
if __name__ == "__main__":
    print(get_project_version())
