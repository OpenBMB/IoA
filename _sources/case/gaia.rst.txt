GAIA Benchmark
=======================================

Let's dive into the GAIA benchmark - a rigorous test designed to challenge AI agents' problem-solving skills!

🤔 What's GAIA?
---------------
`GAIA <https://arxiv.org/abs/2311.12983>`_ is a benchmark that tests AI systems on a wide range of real-world tasks that require a set of fundamental abilities such as reasoning, multi-modality handling, web browsing, and generally tool-use proficiency.

🚀 Let's Get Started!
----------------------

0. Prepare the docker images:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We assume that you have followed the `Instruction <../getting_started/installation.html>`_ to prepare the docker images for the server, client and ReAct agent.

1. Launch the Milvus service:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, we need to launch the Milvus service. It's like the librarian of our AI team, helping to organize and retrieve information quickly.

.. code-block:: bash

    docker-compose -f dockerfiles/compose/milvus.yaml up

2. Launch the server and the client:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   
Now, let's bring our server and client agents online. This command sets up the collaborative environment.

.. code-block:: bash

    docker-compose -f dockerfiles/compose/gaia.yaml up

3. Let the Games Begin!
^^^^^^^^^^^^^^^^^^^^^^^

With everything in place, it's time to start the GAIA benchmark.

.. code-block:: bash

    python scripts/gaia/test_gaia.py --level <level_in_gaia> --max_workers <thread_number>

- Replace :code:`<level_in_gaia>` with your chosen difficulty (1, 2, or 3).
- Set :code:`<thread_number>` to decide how many tasks the team handles simultaneously.
