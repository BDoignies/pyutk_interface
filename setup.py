import setuptools
import sys
import os

from setuptools.command.install import install

def replace(file_path, pattern, subst):
    """
        Replace a pattern in a file
    """
    from tempfile import mkstemp
    from shutil import move, copymode
    from os import fdopen, remove

    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))

    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)

def set_utkdir(src_file="src/pyutk/pyutk.py"):
    """
        Set the UTK directory

        This function will modify the source code of 
        the library to set a proper utk path as default

        This avoid colling pyutk.set_dir every time
        but is an ugly way of configuring a library
    """
    argv = sys.argv
    new_value = '__UTK__DIR__ = ""'
    # TODO : Argparse if possible
    if len(argv) >= 4:
        if argv[2] == "--utk":
            abspath = os.path.abspath(argv[3])
            new_value = f'__UTK__DIR__ = "{abspath}"'
            replace(
                src_file,
                '__UTK__DIR__ = ""',
                new_value
            )
        # Remove both values so setuptools does
        # not cry about it
        sys.argv.pop(2)
        sys.argv.pop(2)

    return new_value

def clean_utkdir(new_value, src_file="src/pyutk/pyutk.py"):
    """
        Reset source code back to default settings
    """
    replace(
        src_file,
        new_value,
        '__UTK__DIR__ = ""',
    )

if __name__ == "__main__":
    new_value = set_utkdir() # TODO : Find the proper way to do this
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

    setuptools.setup(
        name="pyutk",
        version="0.0.1",
        author="Bastien DOIGNIES",
        author_email="bastien.doignies@liris.cnrs.fr",
        description="A python interface to UTK library",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="",
        project_urls={},
        classifiers=[],
        package_dir={"": "src"},
        packages=setuptools.find_packages(where="src"),
        python_requires=">=3.6"
    )

    clean_utkdir(new_value) # TODO : Find the proper way to do this