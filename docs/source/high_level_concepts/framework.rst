Framework Philosophy
########################################

.. _`AutoGPT`: https://github.com/Significant-Gravitas/AutoGPT
.. _`Open Interpreter`: https://github.com/OpenInterpreter/open-interpreter

🌐 Why IoA was designed
=======================

The rapid advancement of LLMs has led to the development of various autonomous agents like `AutoGPT`_, `Open Interpreter`_, etc., each with unique capabilities. However, these agents often operate in isolation, making it challenging to combine their strengths for complex tasks. Inspired by the internet's ability to connect diverse entities, we propose the Internet of Agents (IoA), a framework designed to enable heterogeneous, distributed agents to collaborate effectively.

Key Components
==============

.. figure:: ../_static/layers.png
   :align: center
   :alt: A peek at IoA's layered architecture

Client
------
The client component in IoA serves as a wrapper for individual agents, providing them with the necessary interfaces to communicate within the system. It consists of three main layers:

**Interaction Layer:**
    * **Team Formation Block:** Implements logic for identifying suitable collaborators and forming teams based on task requirements.
    * **Communication Block:** Manages the agent's participation in group chats and handles message processing.

**Data Layer:**
    * **Agent Contact Block:** Stores information about other agents the current agent has interacted with.
    * **Group Info Block:** Maintains details about ongoing group chats and collaborations.
    * **Task Management Block:** Tracks the status and progress of assigned tasks.

**Foundation Layer:**
    * **Agent Integration Block:** Defines protocols and interfaces for integrating third-party agents into the IoA ecosystem.
    * **Data Infrastructure Block:** Handles data storage and retrieval.
    * **Network Infrastructure Block:** Manages network communications with the server.

|

Server
------
The server acts as the central hub of IoA, facilitating agent discovery, group formation, and message routing. Its architecture also consists of three layers:

**Interaction Layer:**
    * **Agent Query Block:** Enables agents to search for other agents based on specific characteristics.
    * **Group Setup Block:** Facilitates the creation and management of group chats.
    * **Message Routing Block:** Ensures efficient and accurate routing of messages between agents and group chats.

**Data Layer:**
    * **Agent Registry Block:** Maintains a comprehensive database of registered agents, including their capabilities and current status.
    * **Session Management Block:** Manages active connections and ensures continuous communication between the server and connected clients.

**Foundation Layer:**
    * **Data Infrastructure Block:** Handles data persistence and retrieval.
    * **Network Infrastructure Block:** Manages network communications.
    * **Security Block:** Implements authentication, authorization, and other security measures.
