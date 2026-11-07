Traceability
============

.. image:: _generated/trace.svg
   :alt: RFLP trace graph

Customer requirements
---------------------

.. needtable::
   :types: crs
   :columns: id, title, satisfies_back as "System requirements", realizes_back as "Use cases", verifies_back as "Acceptance tests"
   :style: table

System requirements
-------------------

.. needtable::
   :types: sysreq
   :columns: id, title, satisfies as "Satisfies", satisfies_back as "Satisfied by", verifies_back as "System tests"
   :style: table

Functions
---------

.. needtable::
   :types: function
   :columns: id, title, realizes as "Realizes", allocated_to as "Allocated to"
   :style: table

Test results
------------

.. needtable::
   :types: testresult
   :columns: id, title, result, tests as "Result of"
   :style: table
