import React from 'react';
import './Message.css';
import getAvatar from '../../utils/avatar';
import ReactMarkdown from 'react-markdown';


function Message({ message }) {
  let type2string = {
    0: "default",
    1: "proposal",
    2: "vote",
    3: "voting result",
    4: "discussion",
    5: "sync task assignment",
    6: "async task assignment",
    7: "inform task result",
    8: "inform task progress",
    9: "pause",
    10: "conclude group discussion",
    11: "conclusion",
  }
  let type = type2string[message.type];
  let nextSpeaker = message.next_speaker;
  if (Array.isArray(nextSpeaker) && nextSpeaker.length !== 0) {
    nextSpeaker = message.next_speaker.join(", ");
  }
  return (
    <div className="message">
      <div className="message-header">
        <img src={`${getAvatar(message.sender)}`} alt={`${message.sender}'s avatar`} className="avatar" />
        <span className="username">{message.sender}</span>
      </div>
      <div className="message-bubble">
        <ReactMarkdown className="message-value">
          {message.content}
        </ReactMarkdown>
        <span className="message-key">Next Speaker: </span>
        <span className='message-value'>{nextSpeaker}</span>
        <br></br>
        <span className="message-key">Type: </span>
        <span className='message-value'>{type}</span>
        <br></br>
        <span className="message-key">Updated Plan: </span>
        <span className='message-value'>{message.updated_plan}</span>
      </div>
    </div>
  );
}

export default Message;
