import React, { useState, useRef } from "react";
import axios from "axios";

const MicIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: 6, verticalAlign: 'middle' }}>
    <rect x="9" y="2" width="6" height="12" rx="3"/>
    <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="22"/>
    <line x1="8" y1="22" x2="16" y2="22"/>
  </svg>
);

// Chat component: main chat UI for interacting with the backend
const Chat = () => {
  // State for chat messages
  const [messages, setMessages] = useState([]);
  // State for user input
  const [input, setInput] = useState("");
  // State for voice recording
  const [recording, setRecording] = useState(false);
  // Ref for speech recognition instance
  const recognitionRef = useRef(null);
  // State for MCP server call/response log
  const [mcpLog, setMcpLog] = useState([]);

  // Send a message to the backend and update chat/mcp log
  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    // Call backend /chat endpoint
    const res = await axios.post("http://localhost:8000/chat", { message: input });
    setMessages((msgs) => [...msgs, { sender: "bot", text: res.data.result }]);
    setMcpLog(res.data.mcp_log || []);
  };

  // Handle Enter key for sending
  const handleInputKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  // Start browser speech recognition
  const startSpeechRecognition = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setRecording(false);
    };
    recognition.onerror = () => {
      setRecording(false);
    };
    recognition.onend = () => {
      setRecording(false);
    };
    recognitionRef.current = recognition;
    setRecording(true);
    recognition.start();
  };

  // Stop browser speech recognition
  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setRecording(false);
    }
  };

  // Render chat UI, input, and MCP log
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fa' }}>
      <div style={{ width: '100%', maxWidth: 480, background: '#fff', border: '1px solid #e3e3e3', borderRadius: 16, boxShadow: '0 4px 24px rgba(0,0,0,0.07)', padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h2 style={{ marginBottom: 24, color: '#1a237e', fontWeight: 700, letterSpacing: 1 }}>Simple Salesforce Chat</h2>
        {/* Chat message history */}
        <div style={{ minHeight: 320, maxHeight: 400, width: '100%', overflowY: "auto", marginBottom: 20, padding: 8, background: '#f4f6fb', borderRadius: 12, boxSizing: 'border-box' }}>
          {messages.map((msg, i) => (
            <div key={i} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "10px 0" }}>
              <span style={{
                display: "inline-block",
                background: msg.sender === "user" ? "#1976d2" : "#e3eafc",
                color: msg.sender === "user" ? "#fff" : "#1a237e",
                borderRadius: 18,
                padding: "10px 18px",
                maxWidth: "80%",
                wordBreak: "break-word",
                fontSize: 16,
                boxShadow: msg.sender === "user" ? "0 2px 8px rgba(25, 118, 210, 0.08)" : undefined
              }}>{msg.text}</span>
            </div>
          ))}
        </div>
        {/* Input and buttons */}
        <div style={{ display: 'flex', width: '100%' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", gap: 10, width: '100%' }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Type your message..."
                style={{ flex: 1, padding: 12, borderRadius: 10, border: "1px solid #b0bec5", fontSize: 16, outline: 'none' }}
              />
              <button
                onClick={sendMessage}
                style={{ padding: "10px 20px", borderRadius: 10, background: "#1976d2", color: "#fff", border: 'none', fontWeight: 600, fontSize: 16, cursor: 'pointer', boxShadow: '0 2px 8px rgba(25, 118, 210, 0.08)' }}
              >
                Send
              </button>
              <button
                onMouseDown={startSpeechRecognition}
                onMouseUp={stopSpeechRecognition}
                onTouchStart={startSpeechRecognition}
                onTouchEnd={stopSpeechRecognition}
                style={{ padding: "10px 20px", borderRadius: 10, background: "#1976d2", color: "#fff", border: 'none', fontWeight: 600, fontSize: 16, cursor: 'pointer', display: 'flex', alignItems: 'center', boxShadow: '0 2px 8px rgba(25, 118, 210, 0.08)' }}
              >
                {recording ? "Listening..." : "Record"}
                <MicIcon />
              </button>
            </div>
          </div>
        </div>
        {/* MCP Server Log below input */}
        <div style={{ width: '100%', marginTop: 18, background: '#f9fafb', border: '1px solid #e3e3e3', padding: 16, borderRadius: 12, maxHeight: 200, overflowY: 'auto' }}>
          <h4 style={{ color: '#1976d2', marginBottom: 12 }}>MCP Server Log</h4>
          {mcpLog.length === 0 && <div style={{ color: '#888', fontSize: 13 }}>No MCP activity yet.</div>}
          {mcpLog.map((entry, idx) => (
            <div key={idx} style={{ marginBottom: 12, fontSize: 13 }}>
              <b>{entry.type === "call" ? "Call" : "Response"}:</b> <span style={{ color: '#333' }}>{entry.tool}</span>
              <pre style={{ background: '#f4f6fb', borderRadius: 6, padding: 8, margin: 0, fontSize: 12, overflowX: 'auto' }}>
                {JSON.stringify(entry.type === "call" ? entry.payload : entry.response, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Chat; 