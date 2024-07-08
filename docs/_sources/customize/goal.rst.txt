#######################
Goal
#######################

|

Create :code:`tests` in the :code:`test_your_case.py` directory. For example, :code:`tests/test_IOT_real.py` 

Goal
===========================
Complete your task objective description in the goal variable, and send a POST request to the :code:`url: "http://127.0.0.1:5050/launch_goal"` ，set :code:`team_member_names` to None, and :code:`team_up_depth`  to the depth of nested teaming you desire.

.. code-block:: python

   import requests 
   goal = """ your task goal """ (ex. """ Complete preparations for  a Halloween themed party. The following is the list of guests, RanLi (vegetarian), WeiZe (fitness enthusiast), YiTong (gluten-free), QianChen (kosher), Chengyang (halal). """)
   response = requests.post(
      "http://127.0.0.1:5050/launch_goal",
      json={
         "goal": goal
         "team_member_names": None
         "team_up_depth": 1
      },
   )