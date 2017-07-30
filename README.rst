instructor (Python struct for humans)
=====================================

Inspired by:

* `structs <https://github.com/jaysonsantos/structs>`_
* `suitcase <https://github.com/digidotcom/python-suitcase>`_
* `starstruct <https://github.com/sprout42/StarStruct>`_
* `cstruct <https://github.com/andreax79/python-cstruct>`_
* `destruct <https://github.com/drdaeman/destruct>`_
* `ezstruct <https://github.com/matthewg/EzStruct>`_

Tested for python 2.7.

Installation
------------

Instructor can be installed with pip:

.. code-block:: shell

    $ pip install instructor

or directly from the source code:

.. code-block:: shell

    $ git clone https://github.com/pikhovkin/instructor.git
    $ cd instructor
    $ python setup.py install

Usage example
-------------
.. code-block:: python

    from instructor.model import InstructorModel
    from instructor import fields

    class Protocol(InstructorModel):
        byte_order = fields.NetworkByteOrder()
        protocol = fields.UInt16(default=1)
        length = fields.UInt32(default=0)
        name = fields.Str(length)

    data = '\x00\x01\x00\x00\x00\x0c\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64\x21'
    p1 = Protocol(data)

    name = 'Hello World!'
    p2 = Protocol(length=len(name), name=name)

    assert p1.protocol == p2.protocol
    assert p1.length == p2.length
    assert p1.name == p2.name

    assert data == p2.pack()
