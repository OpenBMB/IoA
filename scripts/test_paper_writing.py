import requests

goal = """Write the introduction section of a paper about the concept "Internet of Agents" (IoA). Note that the IoA is not the same as the conventional "IoA" in the IoA literature. 
Here's the background of the IoA that we are talking about:
Large models (LMs) demonstrate remarkable capabilities. Recent research has illustrated that when LMs are equipped with specific tools and memory, they become intelligent agents capable of navigating intricate virtual environments and executing difficult tasks. For instance, these agents can utilize calculators to tackle mathematical problems or employ web browsers to gather information and produce reports. These agents function as human assistants, enhancing convenience in our lives.
Building on this concept, we foresee a promising future where every individual and internet-enabled device possesses its own agent. This will revolutionize interactions between humans, between humans and devices, and between devices themselves. We refer to this paradigm shift as the Internet of Agents (IoA), a broader concept than the Internet of Things (IoT). While IoT focuses on the connectivity of devices, IoA emphasizes the transformation in the nature of these interactions. In an IoA world, humans might not need to operate objects directly. Instead, a person's agent can interface with another object's agent to produce the desired result. The agent of that object then performs the relevant action. Furthermore, people's social interactions could evolve as agents help find potential friends based on compatibility. This paints a picture of a society where humans, objects, and their agents harmoniously coexist and bolster each other

The paper is expected to be published in a high-impact journal like Nature or Science. Therefore, when writing the introduction section, it's crucial to adhere strictly to the formatting and citation styles typically required by these journals, which includes providing accurate citations and references for any factual statements, theories, or prior research mentioned. The introduction section should not only be polished and complete but also supported by relevant literature to establish a solid foundation for the paper's topic.
The final output should be the introduction section of the paper.
"""

response = requests.post(
    "http://127.0.0.1:5050/launch_goal",
    json={
        "goal": goal,
        # "team_member_names": [
        #     "Weize Chen's Assistant",
        #     "Chen Qian's Assistant",
        #     "Cheng Yang's Assistant",
        #     "ArxivAssistant",
        # ],
        "team_up_depth": 1,  # the depth limit of nested teaming up
    },
)
print(response)
