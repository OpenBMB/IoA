Goal Submission
#######################
When all agents' Docker containers are successfully configured, sending a POST request to the local server to initiate a goal is necessary process, enabling the IoA to accomplish specific goals. Goal submission serves as a critical startup mechanism to validate the IoA's functionality by setting specific tasks or objectives. By defining these goals, you ensure that the IoA and its integrated agents are working correctly and can effectively perform their intended tasks. This process is essential for verifying the system's capabilities and identifying any potential issues before deploying the IoA in a production environment. Before launching goal, you need to create a Python script.

* Create :code:`test_your_case.py` in the :code:`scripts` directory. For example, :code:`scripts/test_paper_writing.py` 

Goal
===========================
Complete your task objective description in the goal variable, and send a POST request to the :code:`url: "http://127.0.0.1:5050/launch_goal"` ，set :code:`team_member_names` to None, and :code:`team_up_depth`  to the depth of nested teaming you desire.
The full URL :code:`url: "http://127.0.0.1:5050/launch_goal"` is used to send a POST request to the local server to initiate a goal. This request includes a JSON payload specifying the details of the goal, such as the goal description, maximum turns, and team member names and so on. The server at this endpoint processes the request and sets the specified goal for the IoA to accomplish.

.. code-block:: python

   import requests 
   goal = "task descrpition" 
   "(e.g. goal = I want to know the annual revenue of Microsoft from 2014 to 2020. Please generate a figure in text format showing the trend of the annual revenue, and give me a analysis report.)"
   response = requests.post(
      "http://127.0.0.1:5050/launch_goal",
      json={
         "goal": goal,
         "max_turns": 20,
         "team_member_names": [agent_1, agent_2] "(if you have no spcific team members, set it to None)""
         "team_up_depth": "The depth of the nested team-up. Defaults to None.
         "is_collaborative_planning_enabled (bool, optional)": "Whether the collaborative planning is enabled. Defaults to False."
      },
   )