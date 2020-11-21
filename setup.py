import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="acid_vault",
    version="0.0.2",
    author="Nils Nyman-Waara",
    author_email="acid_vault@h2so4.se",
    description="Password Vault",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/svavelsyra/PyVault",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['cryptography>=3.0',
                      'paramiko>=2.7',
                      'pillow>=7.0']
)
