import React, { useState, useEffect } from "react";
import "./App.css";
import GroupList from "./components/GroupList/GroupList";
import ChatWindow from "./components/ChatWindow/ChatWindow";

function App() {
  // Left panel
  const [groups, setGroups] = useState([
    // { comm_id: "1", agent_names: ["asdf", "dfdfdf"] },
    // { comm_id: "2", agent_names: ["Friends"] },
  ]);

  // All right panel data
  const [messages, setMessages] = useState({
    // comm_id: [{
    //   comm_id: "xx",
    //   sender: "xx",
    //   content: "xx",
    //   goal: "xx",
    //   next_speaker: ["xx"],
    //   state: 0,
    //   task_abstract: "",
    //   task_conclusion: "",
    //   task_desc: "",
    //   task_id: "",
    //   team_members: [""],
    //   team_up_depth: 1,
    //   triggers: [],
    // }],
  });
  const [selectedGroup, setSelectedGroup] = useState(null);

  let commID2Name = {};

  function update_message(message) {
    setMessages((prevMessages) => {
      const chatId = message.comm_id;
      const currentMessages = prevMessages[chatId] || [];
      return {
        ...prevMessages,
        [chatId]: [...currentMessages, message],
      };
    });
  }

  useEffect(() => {
    const MAX_RETRIES = 3; // Adjust the maximum retry attempts
    const RETRY_INTERVAL = 3000; // Interval between retries in milliseconds
    let socket; // WebSocket object
    let connectionEstablished = false; // Flag to track connection status

    function connectWebSocket() {
      socket = new WebSocket("ws://127.0.0.1:7788/chatlist_ws");

      // Event Handlers
      socket.onopen = () => {
        console.log("WebSocket connection established!");
        connectionEstablished = true; // Update the flag on successful connection
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data); // Assuming the message is in JSON format
        console.log(message);
        switch (message.frontend_type) {
          case "teamup":
            setGroups((prevGroups) => [
              {
                comm_id: message.comm_id,
                agent_names: message.agent_names,
                team_name: message.team_name || message.agent_names.join(", "),
              },
              ...prevGroups,
            ]);
            commID2Name[message.comm_id] = message.team_name;
            break;
          case "message":
            update_message(message);
            let commId = message.comm_id;
            setGroups((prevGroups) => {
              return prevGroups.map((group) => {
                if (group.comm_id === commId) {
                  group.latest_message = `[${message.sender}]: ${message.content}`;
                }
                return group;
              });
            });
            break;

          default:
            break;
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        connectionEstablished = false; // Update the flag on error
      };

      socket.onclose = (event) => {
        console.log("WebSocket connection closed:", event);
        connectionEstablished = false; // Update the flag on close
      };
    }

    let retries = 0;
    const intervalId = setInterval(() => {
      if (!connectionEstablished && retries < MAX_RETRIES) {
        connectWebSocket();
        retries++;
      } else {
        clearInterval(intervalId); // Stop trying after a successful connection or max retries
      }
    }, RETRY_INTERVAL);

    return () => {
      clearInterval(intervalId);
      if (socket) {
        socket.close(); // Correct method to close the WebSocket
      }
    };
  }, []);

  // Fetch all the chat records from the server when initialized
  useEffect(() => {
    fetch("http://127.0.0.1:7788/fetch_chat_record", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Success:", data);
        let newMessages = {};
        let newGroups = [];
        for (const comm_id in data) {
          let chatRecord = data[comm_id]["chat_record"];
          let agentNames = data[comm_id]["agent_names"];
          let teamName = data[comm_id]["team_name"] || agentNames.join(", ");
          commID2Name[comm_id] = teamName;
          chatRecord.forEach((message) => {
            newMessages[comm_id] = newMessages[comm_id] || [];
            newMessages[comm_id].push(message);
          });

          let latestMessage = chatRecord[chatRecord.length - 1] || null;
          newGroups = [
            {
              comm_id: comm_id,
              agent_names: agentNames,
              latest_message: latestMessage
                ? `[${latestMessage.sender}]: ${latestMessage.content}`
                : "",
              team_name: teamName,
            },
            ...newGroups,
          ];
        }
        setMessages(newMessages);
        setGroups(newGroups);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }, []);

  let selectedMessages = messages[selectedGroup] || [];

  return (
    <div className="app-container">
      <GroupList groups={groups} onGroupSelect={setSelectedGroup} />
      <ChatWindow
        messages={selectedMessages}
        teamName={selectedGroup ? commID2Name[selectedGroup] : "Select a group"}
      />
    </div>
  );
}

export default App;
