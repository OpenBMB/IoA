#######################
Tool
#######################

|

Create and complete the corresponding tool's Python implementation in  :code:`im_client/agents/tools` . For example, :code:`im_client/agents/tools/IOT_tools.py` 

Create a folder named your_tools_name under the :code:`im_client/agents/react` directory. For example, :code:`im_client/agents/react/tools_IOT`

Within the :code:`your_tools_name` folder, create a file named :code:`your_tools_name.yaml` to serve as the configuration file for calling the tool by the tool agent. The format of all tools within the YAML file should adhere to the OpenAI function call format. For example, :code:`tools_IOT/Tools_Drinker.yaml`. Here is an example:

Tool with required parameters
=====================================

.. code-block:: yaml

    - function:
        description: your function description 
        name:function name
        parameters:
          properties:
            parameters_1:
              description:  your parameters_1 description 
              type: string / number / boolean 
              enum: ["It's necessary if your parameter is set by Literal type OR specified parameter"] 
            parameters_2: (It's necessary if there are more than 1 parameter in your function)
              description:  your parameters_1 description 
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
        description: your function description 
        name: function name
        parameters:
          properties: {} 
          required: [] 
          type: object
      type: function
