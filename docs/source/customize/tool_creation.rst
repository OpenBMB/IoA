Tool Creation
#######################
Tool creation is necessary when you do not have your own agent but want to provide a custom tool that a ReAct agent or another existing agent can utilize to solve problems. This need arises when you have specialized tools or functionalities that can enhance the capabilities of an agent without the need to develop a full-fledged new agent. By integrating these tools, the ReAct agent can leverage them to perform specific tasks, thereby extending its problem-solving abilities and making it more versatile and effective in handling a broader range of scenarios. Before introduce the configuration of tools, it is necessary to create a yaml file and corresponding tool's Python file for the tool configuration.

* Create and complete the corresponding tool's Python implementation in  :code:`im_client/agents/tools`. For example, :code:`im_client/agents/tools/code_executor.py` 
  
* Import and  Add the completed tool to the :code:`TOOL_MAPPING` in the :code:`im_client/agents/tools/__init__.py`, ensuring the tool is called successfully. For example:

  .. code-block:: python

      from . import arxiv_tools
      TOOL_MAPPING = {
      "arxiv_search": arxiv_tools.arxiv_search
      }

* Create a file named :code:`tools_name.yaml` to serve as the configuration file for calling the tool by the tool agent. The format of all tools within the YAML file should adhere to the OpenAI function call format. For example, :code:`im_client/agents/react/tools_code_executor.yaml`. 
  
Here is an example for yaml configuration:

Tool with required parameters
=====================================

.. code-block:: yaml

    - function:
        description: function description 
        name: function name
        parameters:
          properties:
            parameters_1:
              description:  parameters_1 description 
              type: string / number / boolean 
              enum: ["It's necessary if parameter is set by Literal type OR specified parameter"] 
            parameters_2:  # It's necessary if there are more than 1 parameter in function
              description:  parameters_2 description 
              type: string / number / boolean 
          required:
          - parameters_1
          - parameters_2
          type: object
      type: function

|

Tool without required parameters
=========================================

.. code-block:: yaml

    - function:
        description: function description 
        name: function name
        parameters:
          properties: {} 
          required: [] 
          type: object
      type: function
