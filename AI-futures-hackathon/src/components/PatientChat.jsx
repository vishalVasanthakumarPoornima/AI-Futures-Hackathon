import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

function PatientChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [done, setDone] = useState(false);
  const [lastBotIndex, setLastBotIndex] = useState(null);
  const [summary, setSummary] = useState("");
  const [docQAActive, setDocQAActive] = useState(false);
  const [docQ, setDocQ] = useState("");
  const [docA, setDocA] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    const resetAndInit = async () => {
      try {
        await axios.post("http://localhost:8000/reset");
        const firstQuestion = "Are you ready to get your medical history recorded?";
        setMessages([
          { sender: "bot", text: "Welcome to the Patient Intake Chat. Let's get started!" },
          { sender: "bot", text: firstQuestion },
        ]);
        setLastBotIndex(1);
      } catch (error) {
        console.error("Initialization failed:", error);
        setMessages([{ sender: "bot", text: "Error initializing chat. Please try again later." }]);
      }
    };
    resetAndInit();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = input.trim();
    const newMessages = [...messages, { sender: "user", text: userMessage }];
    setMessages(newMessages);
    setInput("");

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        user_message: userMessage,
        follow_up: false,
      });

      if (!response.data || !response.data.response) {
        throw new Error("Invalid response from server");
      }

      const botReply = response.data.response;
      const newMessagesWithBot = [...newMessages, { sender: "bot", text: botReply }];
      setMessages(newMessagesWithBot);
      setLastBotIndex(newMessagesWithBot.length - 1);
      if (response.data.done) setDone(true);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [...prev, { sender: "bot", text: "There was an error sending your message. Please try again." }]);
    }
  };

  const downloadPDF = async () => {
    try {
      const res = await axios.get("http://localhost:8000/download_pdf", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "patient_summary.pdf");
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error("PDF download failed:", error);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await axios.get("http://localhost:8000/summary");
      setSummary(res.data.summary);
    } catch (error) {
      console.error("Summary fetch failed:", error);
      setSummary("There was an error generating the summary.");
    }
  };

  const handleDocUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      await axios.post("http://localhost:8000/upload_doc", formData);
      setDocQAActive(true);
    } catch (err) {
      console.error("Error uploading document:", err);
    }
  };

  const handleDocQuestion = async () => {
    try {
      const res = await axios.post("http://localhost:8000/ask_doc", { question: docQ });
      setDocA(res.data.answer);
    } catch (err) {
      setDocA("Error retrieving answer.");
      console.error("Document QA failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-900 via-indigo-900 to-black text-white p-4">
      <div className="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto">
        <div className="flex-1 border rounded-lg p-6 bg-black/30 backdrop-blur-md">
          <h1 className="text-3xl font-bold mb-4 text-center text-purple-200">Patient Intake Chat</h1>
          <div className="h-[500px] overflow-y-auto mb-4 pr-2">
            {messages.map((msg, idx) => (
              <div key={idx} className={`mb-3 w-full flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] px-4 py-3 rounded-xl text-sm shadow-md break-words ${msg.sender === "user" ? "bg-blue-600 text-white" : "bg-red-800 text-white"}`}>
                  <p>{msg.text}</p>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-black/20 text-white border border-white/20 px-4 py-2 rounded-md focus:outline-none"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer here..."
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button
              onClick={sendMessage}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md"
            >
              Send
            </button>
          </div>
          {done && (
            <div className="mt-4 flex flex-col items-center gap-3">
              <button
                onClick={downloadPDF}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
              >
                📄 Download Patient Summary PDF
              </button>
              <button
                onClick={fetchSummary}
                className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-md"
              >
                🧠 Show Conversation Summary
              </button>
              <label className="text-sm mt-4">
                📄 Upload Document for QA:
                <input type="file" onChange={handleDocUpload} className="block mt-2" />
              </label>
              {docQAActive && (
                <div className="mt-4 w-full">
                  <input
                    value={docQ}
                    onChange={(e) => setDocQ(e.target.value)}
                    placeholder="Ask a question about the uploaded document"
                    className="w-full mt-2 px-3 py-2 text-black rounded"
                  />
                  <button
                    onClick={handleDocQuestion}
                    className="mt-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                  >
                    Ask
                  </button>
                  {docA && (
                    <div className="mt-2 bg-white/10 p-3 rounded text-sm text-white">
                      <strong>Answer:</strong> {docA}
                    </div>
                  )}
                </div>
              )}
              {summary && (
                <div className="mt-4 bg-black/40 text-sm p-4 rounded border border-white/10 max-h-64 overflow-y-auto w-full">
                  <h2 className="text-lg font-semibold mb-2 text-yellow-300">Conversation Summary:</h2>
                  <p>{summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PatientChat;
