import React, { useState, useEffect, useRef, useCallback } from "react";
import Message from "../Message/Message"; // Assuming you have a Message component
import "./ChatWindow.css"; // Assuming you have a CSS file
import ReactMarkdown from 'react-markdown';

function ChatWindow({ messages, teamName }) {
  const [displayMessages, setDisplayMessages] = useState([]);
  const [newMessageText, setNewMessageText] = useState("");
  const [shouldScroll, setShouldScroll] = useState(false);
  const scrollRef = useRef(null);


  useEffect(() => {
    console.log(messages);
    const isAtBottom = (() => {
      if (!scrollRef.current) return false;

      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const threshold = 5; // Margin of error for the bottom check
      return scrollTop >= scrollHeight - clientHeight - threshold;
    });
    setShouldScroll(isAtBottom());
    if (messages) {
      setDisplayMessages(messages);
    }

  }, [messages]);

  useEffect(() => {
    const scrollToBottom = (() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });

    if (shouldScroll) {
      scrollToBottom();
    }
  }, [displayMessages]);

  const handleInputChange = (event) => {
    setNewMessageText(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // Logic to send the new message (update state, API call, etc.)
    setNewMessageText("");
  };

  const title = teamName;

  return (
    <div className="chat-window">
      <div className="chat-messages" ref={scrollRef}>
        {displayMessages.length > 0 && (
          <div className="chat-goal">
            <span className="chat-goal-title">Goal:</span>
            <ReactMarkdown className="chat-goal-content">
              {displayMessages[0].goal}
            </ReactMarkdown>
          </div>
        )}
        {displayMessages.map((message, index) => (
          <Message key={message.comm_id + "-" + index} message={message} />
        ))}
      </div>
      {/* <form className="message-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={newMessageText}
          onChange={handleInputChange}
          placeholder="Type your message..."
        />
        <button type="submit">Send</button>
      </form> */}
    </div >
  );
}

export default ChatWindow;
