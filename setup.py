from setuptools import find_packages, setup


setup(
    name="blackbox-cli",
    version="0.0.1",
    description="Tool for automatic backups of databases",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Leon Sandøy",
    author_email="leon.sandoy@gmail.com",
    url="https://github.com/lemonsaurus/blackbox",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Topic :: Database",
        "Topic :: System :: Archiving :: Backup"
    ],
    # Remember to update this with the contents of the Pipfile
    install_requires=[
        "pyyaml~=5.3.1",
        "requests~=2.25.1",
        "boto3~=1.16.51",
        "loguru~=0.5.3",
        "jinja2==2.11.2",
    ],
    python_requires='~=3.9',
    extras_require={},
    include_package_data=True,
    zip_safe=False
)
