Collaborative Paper Writing
##########################################

Let's try out an interesting and simple example of IoA at work: drafting the introduction of the research paper of IoA.

✍️ Paper Writing with IoA
=========================

Picture this: Four AI assistants sitting around a virtual table, brainstorming and crafting the perfect introduction for a paper about IoA itself. Here's our dream team:

1. Weize Chen's Assistant
2. Chen Qian's Assistant
3. Cheng Yang's Assistant
4. ArxivAssistant (our research guru)

ArxivAssistant is the bookworm of the group. Built on a ReAct agent framework, it's an expert at digging up relevant papers from Arxiv to support our writing.

⚙️ Try it out
--------------------------------

Ready to see these agents in action? Follow these simple steps:

1. Launch the Milvus service:

First, we need to launch the Milvus service. It's like the librarian of our AI team, helping to organize and retrieve information quickly.

.. code-block:: bash

    docker-compose -f dockerfiles/compose/milvus.yaml up

2. Create the ReAct Agent image:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash
  
  docker pull weize/react-agent:latest
  docker tag weize/react-agent:latest react-agent:latest

    # or 
    # docker build -f dockerfiles/tool_agents/react.Dockerfile -t react-agent:latest . 

3. Set up your credentials:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   
Add your OpenAI API key and other environment variables to :code:`dockerfiles/compose/.env`. 

.. note:: If you've already set these as system environment variables, you can skip this step!

4. Launch the IoA writing squad:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  docker-compose -f dockerfiles/compose/paper_writing.yml up --build

5. Kickstart the writing process:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a new command line window, run:

.. code-block:: bash

  python scripts/test_paper_writing.py

And there you have it! You've just initiated an AI-powered writing collaboration.

.. |

.. Paper Writing with Printer
.. ====================================
.. IOA Paper Writing with Printer builds on the Paper Writing scenario, introducing the FormatCraft Printer which can print out the result of the IOA paper introduction completed in the Paper Writing scenario. Here’s how to start and use it:

.. 1. First, create the ReAct Agent image.

..    .. code-block:: bash

..      docker build -f dockerfiles/tool_agents/latex_printer_react.Dockerfile  -t latex_printer_react:latest .


.. |

.. 2. Create a network that allows docker containers to communicate with each other.

..    .. code-block:: bash

..      docker network create agent_network


.. |

.. 3. Start the containers specified in the docker-compose configuration file.

..    .. code-block:: bash

..      docker-compose -f dockerfiles/compose/paper_writing_with_printer.yml up --build


.. |

.. 4. After starting, execute a command in another window command line, which will initiate a goal.

..    .. code-block:: bash

..      python tests/test_paper_writing_with_printer.py
