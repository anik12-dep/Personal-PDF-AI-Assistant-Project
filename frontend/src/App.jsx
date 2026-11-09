import { useEffect, useRef, useState } from "react";
import {
  Plus,
  MessageSquare,
  Upload,
  Send,
  FileText,
  Bot,
  User,
  LoaderCircle,
  Sun,
  Moon,
} from "lucide-react";

import {
  createConversation,
  getConversations,
  getConversationHistory,
  uploadPDF,
  sendMessage,
} from "./api";

import "./App.css";

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [pdfName, setPdfName] = useState("");
  const [darkMode, setDarkMode] = useState(false);

  const fileInput = useRef(null);

  // Load conversations
  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    try {
      console.log("Testing backend connection...");

      const data = await getConversations();

      console.log("Backend Response:", data);
      console.log("Conversations:", data.conversations);

      setConversations(data.conversations || []);

      if (data.conversations?.length > 0) {
        await openConversation(data.conversations[0].conversation_id);
      } else {
        await newChat();
      }
    } catch (error) {
      console.error("Backend Connection Error:", error);
      console.error("Error Response:", error.response?.data);
      console.error("Error Status:", error.response?.status);

      alert("Backend connection failed! Check console.");
    }
  }

  async function newChat() {
    try {
      const data = await createConversation();

      console.log("New conversation:", data);

      setActiveId(data.conversation_id);
      setMessages([]);
      setPdfName("");

      const updated = await getConversations();
      setConversations(updated.conversations);
    } catch (error) {
      console.error("Create Conversation Error:", error);

      alert(
        error.response?.data?.detail ||
          error.message ||
          "Could not create conversation!",
      );
    }
  }

  // Open previous conversation
  async function openConversation(id) {
    try {
      setActiveId(id);

      const data = await getConversationHistory(id);

      setMessages(
        data.history.map((message) => ({
          role: message.role,
          content: message.content,
          sources: [],
        })),
      );
    } catch {
      alert("Could not load conversation!");
    }
  }

  // Upload PDF
  async function handleUpload(event) {
    const file = event.target.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please select a PDF file.");
      return;
    }

    setUploading(true);

    try {
      const data = await uploadPDF(file);
      setPdfName(data.filename);

      alert(`PDF uploaded successfully! ${data.total_chunks} chunks created.`);
    } catch (error) {
      alert(error.response?.data?.detail || "PDF upload failed!");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  // Send message
  async function handleSend() {
    const text = question.trim();

    if (!text || loading) return;

    if (!activeId) {
      alert("Please create a conversation first.");
      return;
    }

    setQuestion("");

    setMessages((previous) => [...previous, { role: "user", content: text }]);

    setLoading(true);

    try {
      const data = await sendMessage(activeId, text);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);

      const updated = await getConversations();
      setConversations(updated.conversations);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            error.response?.data?.detail ||
            "Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`app ${darkMode ? "dark" : "light"}`}>
      <aside className="sidebar">
        <h2>PDF AI Assistant</h2>

        <button className="new-chat" onClick={newChat}>
          <Plus size={18} /> New Chat
        </button>

        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>

        <p className="side-heading">YOUR CONVERSATIONS</p>

        {conversations.map((item) => (
          <div
            key={item.conversation_id}
            className="conversation"
            onClick={() => openConversation(item.conversation_id)}
          >
            <MessageSquare size={17} />
            <span>{item.title || "New Conversation"}</span>
          </div>
        ))}

        <div className="sidebar-bottom">Personal PDF Assistant</div>
      </aside>

      <main className="main">
        <header className="header">
          <Bot size={22} />
          <span>Personal PDF AI Assistant</span>
        </header>

        <section className="chat-area">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="bot-icon">
                <Bot size={35} />
              </div>

              <h1>Chat with your PDF</h1>

              <p>
                Upload your PDF and ask anything. Your AI assistant is ready to
                help.
              </p>

              <button
                className="upload-button"
                onClick={() => fileInput.current.click()}
                disabled={uploading}
              >
                <Upload size={18} />
                {uploading ? "Uploading..." : "Upload PDF"}
              </button>
            </div>
          )}

          {pdfName && (
            <p className="pdf-status">
              <FileText size={16} /> {pdfName}
            </p>
          )}

          {messages.map((message, index) => (
            <div
              className={`message ${
                message.role === "user" ? "user-message" : "assistant-message"
              }`}
              key={index}
            >
              <div className="bot-icon small">
                {message.role === "user" ? (
                  <User size={20} />
                ) : (
                  <Bot size={20} />
                )}
              </div>

              <div>
                <strong>
                  {message.role === "user" ? "You" : "AI Assistant"}
                </strong>

                <p className="message-text">{message.content}</p>

                {message.sources?.length > 0 && (
                  <div className="sources">
                    <strong>Sources:</strong>

                    {message.sources.map((source, i) => (
                      <div key={i}>
                        <FileText size={14} />
                        {source.pdf} — Page {source.page}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="loading">
              <LoaderCircle size={18} />
              AI is thinking...
            </div>
          )}
        </section>

        <div className="input-area">
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,application/pdf"
            hidden
            onChange={handleUpload}
          />

          <div className="input-box">
            <button
              title="Upload PDF"
              onClick={() => fileInput.current.click()}
              disabled={uploading}
            >
              <FileText size={20} />
            </button>

            <input
              type="text"
              placeholder="Ask anything about your PDF..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />

            <button
              className="send-button"
              onClick={handleSend}
              disabled={loading || !question.trim()}
            >
              <Send size={19} />
            </button>
          </div>

          <p>AI can make mistakes. Verify important information.</p>
        </div>
      </main>
    </div>
  );
}

export default App;
