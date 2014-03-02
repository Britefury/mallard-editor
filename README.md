Mallard Editor
============

This software is currently in the prototype stage.

Getting started
============

The simplest way to try the editor out is to download a standalone JAR file and run it (you will need Java).


Developing
========

Do develop the Mallard Editor, you will need to get the Larch Environment from
http://www.larchenvironment.com.

You can use either the binary ZIP (in which case you will need to install Jython as well)
or the Larch stand-along JAR.

Larch ZIP
--------

To use the Larch binary ZIP distribution, edit the maledit_bin shell script (POSIX) or the maledit_bin.bat (Windows)
and set the path to where you unzipped larch. Start the Mallard editor with:

	./maledit_bin


Larch JAR
--------

To use the Larch binary JAR distribution, edit the maledit_jar shell script (POSIX) or the maledit_jar.bat (Windows)
and set the path to your Larch JAR file. Start the Mallard editor with:

	./maledit_jar


Building
=======

To build a Mallard Editor JAR, you will need:

- ant
- A Larch stand-alone JAR distribution

Ensure that the Larch JAR is in the Mallard Editor directory

Build with:

	ant -Dlarch.version={{larch version}} -Dmaledit.version={{mallard editor version}}

For example, to use Larch 0.1.33-alpha to create Mallard Editor version 0.1, ise:

	ant -Dlarch.version=0.1.33-alpha -Dmaledit.version=0.1





