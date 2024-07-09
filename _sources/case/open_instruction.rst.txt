Open Instruction Dataset
========================

Let's explore our curated open instruction dataset - a diverse collection of tasks designed to test the versatility of AI agents!

🤔 What's the Open Instruction Dataset?
---------------------------------------
This dataset consists of a wide range of open-ended instructions, challenging AI systems to perform tasks across various domains such as information retrieval, coding, mathematical problem-solving, and general assistance.

🚀 Let's Get Started!
---------------------

0. Prepare the docker images:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We assume that you have followed the `Installation Instructions <../getting_started/installation.html>`_ to prepare the docker images for the server client, **AutoGPT and Open Interpreter**.

1. Launch the Milvus service:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, we need to launch the Milvus service to help manage and retrieve information efficiently:

.. code-block:: bash

    docker-compose -f dockerfiles/compose/milvus.yaml up

2. Launch the server and the clients:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, let's bring our server and client agents online, including AutoGPT and Open Interpreter:

.. code-block:: bash

    docker-compose -f dockerfiles/compose/open_instruction.yaml up

3. Start the Open Instruction test:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With everything set up, it's time to run the open instruction dataset:

.. code-block:: bash

    python scripts/open_instruction/test_open_instruction.py

This script will send the instructions from our curated dataset to the IoA framework, allowing you to observe how AutoGPT and Open Interpreter collaborate to tackle a variety of open-ended tasks.

🎭 Watch the Collaboration Unfold
---------------------------------
As the test runs, you'll see AutoGPT and Open Interpreter work together, leveraging their unique capabilities to address a wide range of instructions. This demonstrates the power of IoA in integrating different AI agents to solve diverse, open-ended problems.

Feel free to examine the outputs and see how the agents complement each other in handling various types of tasks. This test showcases the flexibility and adaptability of the IoA framework in real-world scenarios!