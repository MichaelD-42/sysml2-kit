Seat switch RFQ
===============

Example RFQ project for sysml2-kit: an OEM's request for the seat adjustment switches of one vehicle
line, answered from the seat-switch platform in ``platform/``. Customer requirements (Markdown) are
classified; functional ones are matched by platform features, non-functional ones and constraints are
satisfied by constraints over the platform's rated attributes. Each seat position selects a housing
side and a button set. System and acceptance tests verify the model and implement the customer's own
test requirements; compliance statements answer what the platform does not offer.

.. toctree::
   :maxdepth: 2

   customer/requirements
   customer/test-requirements
   customer/statements
   traceability
   compliance
   model
   acceptance/tests
