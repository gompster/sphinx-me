#!/usr/bin/env python

from __future__ import with_statement
from __future__ import print_function
from datetime import datetime
from os.path import abspath, dirname, exists, join, isdir, splitext
from os import chdir, getcwd, listdir, mkdir, sep
from subprocess import Popen, PIPE
import sys

try:
    input = raw_input
    str = unicode
except NameError:
    pass


__version__ = "0.2.1"


def install():
    """
    Main entry point for running sphinx_me as a script.
    Creates a docs directory in the current directory and adds the
    required files for generating Sphinx docs from the project's
    README file - a conf module that calls setup_conf() from this
    module, and an index file that includes the project's README.
    """
    for name in listdir(getcwd()):
        if splitext(name)[0].upper() == "README":
            readme = name
            break
    else:
        print()
        print("ABORT: No README file in the current directory.")
        return

    docs_path = join(getcwd(), "docs")
    if not isdir(docs_path):
        mkdir(docs_path)
    with open(join(docs_path, "index.rst"), "w") as f:
        f.write(".. include:: ../%s" % readme)
    with open(join(docs_path, "conf.py"), "w") as f:
        f.write("# This file is automatically generated via sphinx-me\n")
        f.write("from sphinx_me import setup_conf; setup_conf(globals())\n")
    print()
    print("SUCCESS: Sphinx docs layout created in %s" % docs_path)
    try:
        import sphinx
    except ImportError:
        print()
        print("Sphinx not installed. Not building docs.")
    else:
        build_path = join(docs_path, "build")
        Popen(["sphinx-build", docs_path, build_path]).wait()
        print()
        print("Docs built in %s" % build_path)


def decode_utf8(s):
    if not isinstance(s, str):
        return str(s, encoding='utf-8')
    return s


def get_version(module):
    """
    Attempts to read a version attribute from the given module that
    could be specified via several different names and formats.
    """
    version_names = ["__version__", "get_version", "version"]
    version_names.extend([name.upper() for name in version_names])
    for name in version_names:
        try:
            version = getattr(module, name)
        except AttributeError:
            continue
        if callable(version):
            version = version()
        try:
            version = ".".join([str(i) for i in version.__iter__()])
        except AttributeError:
            pass
        return version


def get_setup_attribute(attribute, setup_path):
    """
    Runs the project's setup.py script in a process with an arg that
    will print out the value for a particular attribute such as author
    or version, and returns the value.
    """
    args = ["python", setup_path, "--%s" % attribute]
    return Popen(args, stdout=PIPE).communicate()[0].decode('utf-8').strip()


def setup_conf(conf_globals):
    """
    Setup function that is called from within the project's
    docs/conf.py module that takes the conf module's globals() and
    assigns the values that can be automatically determined from the
    current project, such as project name, package name, version and
    author.
    """
    project_path = abspath(join(dirname(conf_globals["__file__"]), ".."))
    chdir(project_path)
    sys.path.insert(0, project_path)
    authors_file = "AUTHORS"
    version = None
    author = None
    setup = "setup.py"
    setup_path = join(project_path, setup)
    ignore = (setup,)

    # First try and get the author and version from setup.py
    if exists(setup_path):
        try:
            import setuptools
        except ImportError:
            pass
        else:
            version = get_setup_attribute("version", setup_path)
            if version == "0.0.0":
                version = None
            author = get_setup_attribute("author", setup_path)
            if author == "UNKNOWN":
                author = None

    # Iterate through each of the files in the project's directory,
    # looking for an AUTHORS file for the project's author, or
    # importable packages/modules for the version.
    for name in listdir(project_path):
        path = join(project_path, name)
        if name.upper() == authors_file:
            with open(path, "r") as f:
                for line in f.readlines():
                    line = line.strip("*- \n\r\t")
                    if line:
                        author = decode_utf8(line)
                        break
        elif name not in ignore and (isdir(path) or splitext(name)[1] == ".py"):
            try:
                module = __import__(name)
            except (ImportError, ValueError):
                continue
            if not version:
                version = get_version(module)
            if version and not author:
                try:
                    author = decode_utf8(getattr(module, "__author__"))
                except AttributeError:
                    pass

    # Ask for any values that couldn't be found.
    if not version:
        version = input("No version number found, please enter one: ")
    if not author:
        author = input("No author found, please enter one: ")
        author = decode_utf8(author)
        with open(join(project_path, authors_file), "wb") as f:
            f.write(author.encode('utf-8'))

    # Inject the minimum required names into the conf module.
    settings = {
        "version": version,
        "release": version,
        "project": project_path.rstrip(sep).split(sep)[-1],
        "master_doc": "index",
        "copyright": "%s, %s" % (datetime.now().year, author),
    }
    pad = max([len(k) for k in settings.keys()]) + 3
    print()
    print("sphinx-me using the following values:")
    print()
    print("\n".join([(k + ":").ljust(pad) + v for k, v in settings.items()]))
    print()
    conf_globals.update(settings)


if __name__ == "__main__":
    install()
