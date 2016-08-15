===================
Vagga in VirtualBox
===================

:Status: PoC

This is a prototype which brings vagga as the first-class tool to OS X and
(possibly) windows using virtualbox


Installation
============

Currently it's (you need python >= 3.4)::

    $ brew install python3 unison unox
    $ pip3 install git+http://github.com/tailhook/vagga-box
    [ .. snip .. ]
    $ vagga
    Available commands:
        run



Short FAQ
=========

**Why is it in python?** For a quick prototype. It will be integrated into
vagga as soon as is proven to be useful. Or may be we leave it in python if
it would be easier to install.

**So should I try this version or wait it integrated in vagga?** Definitely you
should. The integrated version will work the same.

**Is there any difference between this and vagga on linux?** There are two key
differences:

* you need to export ports that you want to be accessible from the
host system
* we keep all the container files (and a copy of the project) in the virtualbox
  to view it from the host system mount nfs volume

__ https://github.com/tailhook/vagga/issues/269

.. code-block:: yaml

    containers:
      django:
        setup:
        - !Alpine v3.3
        - !Py3Install ['Django >=1.9,<1.10']

    commands:
      run: !Command
        description: Start the django development server
        container: django
        _expose-ports: [8080]
        run: python3 manage.py runserver

**Please report if you find any other differences using the tool**. Ah, but
exact text of some error messages may differ, don't be too picky :)

**Why `_expose-dirs` are underscored?** This is a standard
way to add extension metadata or user-defined things in vagga.yaml. We will
remove the underscore as soon as integrate it into main code. Fixing
underscores isn't going to be a big deal.

**Will linux users add `_expose-ports` for me?** Frankly,
currently probably now. But it's small change that probably no one will need
to delete. In the future we want to apply ``seccomp`` filters to allow to bind
only exposed ports on linux too.

**What will be changed when we integrate this into vagga?** We will move more
operations from virtualbox into host system. For example list of commands will
be executed by mac os. Also ``vagga _list``, some parts of ``vagga _clean`` and
so on. But we will do our best to keep semantics exactly the same.


LICENSE
=======

This project has been placed into the public domain.
