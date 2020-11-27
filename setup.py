import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

meta_data = {}
with open('acid_vault/version.py') as fh:
    exec(fh.read(), meta_data)

setuptools.setup(
    name=meta_data['__title__'],
    version=meta_data['__version__'],
    author=meta_data['__author__'],
    author_email=meta_data['__email__'],
    description=meta_data['__summary__'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=meta_data["__uri__"],
    packages=setuptools.find_packages(),
    package_data={'acid_vault': ['*.pyw']},
    include_package_data=True,
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
