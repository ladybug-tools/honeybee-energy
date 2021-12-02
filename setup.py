import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# TODO: put back this code if I ever figure out how to include it in semantic deployment
#  with open('standards-requirements.txt') as f:
#      standards_requirements = f.read().splitlines()

standards_requirements = 'honeybee-energy-standards==2.2.1'

setuptools.setup(
    name="honeybee-energy",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="Ladybug Tools",
    author_email="info@ladybug.tools",
    description="Energy simulation library for honeybee.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ladybug-tools/honeybee-energy",
    packages=setuptools.find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'standards': standards_requirements
    },
    entry_points={
        "console_scripts": ["honeybee-energy = honeybee_energy.cli:energy"]
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent"
    ],
    license="AGPL-3.0"
)
