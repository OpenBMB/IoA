import React, { useState } from "react";
import "./GroupList.css"; // Assuming you have a CSS file
import getAvatar from "../../utils/avatar";

function AvatarGrid({ members }) {
  const getGridClass = () => {
    const count = members.length;
    if (count === 1) return "avatar-grid-one";
    if (count === 2) return "avatar-grid-two";
    if (count === 3) return "avatar-grid-three";
    return "avatar-grid-four"; // For four or more avatars
  };

  return (
    <div className={`avatar-square ${getGridClass()}`}>
      {members.slice(0, 4).map((name, index) => (
        <img
          key={index}
          src={getAvatar(name)}
          alt={`Avatar of ${name}`}
          className={`avatar-group-list avatar-${index}`}
        />
      ))}
    </div>
  );
}



function GroupList({ groups, onGroupSelect }) {
  const [selectedId, setSelectedId] = useState(null);

  const handleChatClick = (chatId) => {
    setSelectedId(chatId);
    onGroupSelect(chatId);
  };

  return (
    <div className="chat-list">
      <ul>
        {groups.map((group) => (
          <li
            key={group.comm_id}
            onClick={() => handleChatClick(group.comm_id)}
            className={selectedId === group.comm_id ? "chat-item-selected" : "chat-item"}
          >
            <AvatarGrid members={group.agent_names} />
            <div className="group-info">
              <span className="group-name">{group.team_name}</span>
              <span className="group-description">{group.latest_message}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default GroupList;
