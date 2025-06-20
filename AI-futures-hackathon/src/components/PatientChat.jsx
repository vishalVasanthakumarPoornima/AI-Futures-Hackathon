import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Popup from './ui/Popup';
import LargePopup from './ui/LargePopup';
import '../index.css';

function PatientChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [done, setDone] = useState(false);
  const [summary, setSummary] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [docQAActive, setDocQAActive] = useState(false);
  const [docQ, setDocQ] = useState("");
  const [docA, setDocA] = useState("");
  const chatEndRef = useRef(null);

  const [followUpQ, setFollowUpQ] = useState("");
  const [analysisQ, setAnalysisQ] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);


  useEffect(() => {
    const resetAndInit = async () => {
      try {
        await axios.post("http://localhost:8000/reset");
        const firstQuestion = "Are you ready to get your medical history recorded?";
        setMessages([
          { sender: "bot", text: "Welcome to the Patient Intake Chat. Let's get started!" },
        ]);
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

      const botReply = response.data.response;
      const newMessagesWithBot = [...newMessages, { sender: "bot", text: "", fullText: botReply }];
      setMessages(newMessagesWithBot);
      if (response.data.done) setDone(true);

      let i = 0;
      const typing = setInterval(() => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.sender === "bot") {
            last.text = last.fullText.slice(0, i + 1);
          }
          return updated;
        });
        i++;
        if (i >= botReply.length) clearInterval(typing);
      }, 15);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [...prev, { sender: "bot", text: "There was an error sending your message." }]);
    }
  };

  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState("");

  const openPopup = () => setIsPopupOpen(true);
  const closePopup = () => setIsPopupOpen(false);


  const handleAnalysis = async () => {
    console.log("test1");
    if(!analysisQ.trim())
      console.log("aate");

    try {
      const res = await axios.post("http://localhost:8000/analysis", {
        sym: analysisQ,
      });
      
      const analysisAnswer = res.data.answer;
      console.log("test");
      console.log(analysisAnswer);
      setAnalysis(analysisAnswer);
    } catch (error) {
      console.log("test3");
      console.error("Summary fetch failed:", error);
      setAnalysis("There was an error generating the summary.");
    }
  };

  const handleFollowUp = async () => {
    if (!followUpQ.trim()) return;
  
    const userAnswers = messages.filter((msg) => msg.sender === "user").length - 1;
    setIsSubmitting(true);
  
    try {
      const res = await axios.post("http://localhost:8000/follow_up", {
        ref_index: userAnswers,
        question: followUpQ,
      });
  
      const followUpAnswer = res.data.answer;  
      setMessages((prev) => [
        ...prev,
        { sender: "user", text: followUpQ },
        { sender: "bot", text: followUpAnswer },
      ]);
      setFollowUpQ(""); // clear input
    } catch (err) {
      console.error("Follow-up failed:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Follow-up failed. Please try again." },
      ]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const downloadPDF = async () => {
    try {
      const res = await axios.get("http://localhost:8000/download_pdf", { responseType: "blob" });
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
      setDocA(res.data.summary);
    } catch (err) {
      setDocA("Error retrieving answer.");
      console.error("Document QA failed:", err);
    }
  };

  return (
    <div style={{ fontFamily: 'Concert One, sans-serif' }} className="min-h-screen bg-gradient-to-br from-red-900 via-indigo-700 to-black text-white p-4">
      <div className="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto">
        <div className="flex-1 border rounded-lg p-6 bg-black/30 backdrop-blur-md">
          <h1 style={{ fontFamily: 'Lexend, sans-serif' }} className="font-lexend text-3xl font-medium mb-4 text-center text-purple-200">Patient Intake Chat</h1>
          <div className="h-[500px] overflow-y-auto mb-4 pr-2">
            {messages.map((msg, idx) => (
              <div key={idx} className={`mb-3 w-full flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                <div style={{ fontFamily: 'Concert One, sans-serif' }} className={`max-w-[75%] px-4 py-3 rounded-xl text-sm shadow-md break-words ${msg.sender === "user" ? "bg-indigo-400 bg-opacity-50 text-white" : "bg-red-700 bg-opacity-50 text-white"}`}>
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
              className="inline-block p-3 bg-gradient-to-br from-green-400 to-blue-600 hover:bg-gradient-to-bl from-red-400 to-blue-600 rounded-md"
            >
              Send
            </button>
            <button onClick={openPopup} className="inline-block p-3 bg-gradient-to-bl from-green-400 to-blue-600 hover:bg-gradient-to-br from-green-400 to-blue-600 rounded-md">
              Follow-Up
            </button>
            <button
        onClick={() => setIsOpen(true)}
        className="inline-block p-3 bg-gradient-to-br from-red-400 to-blue-500 hover:bg-gradient-to-bl from-red-400 to-red-500 rounded-md"
        >
        Immediate Analysis
      </button>

      <LargePopup isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Symptom Analysis</h2>
        <input
    type="text"
    value={analysisQ}
    onChange={(e) => setAnalysisQ(e.target.value)}
    onKeyDown={(e) => e.key === "Enter" && handleFollowUp()}
    className="flex-1 px-4 py-2 text-black border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
    placeholder="Enter your symptoms"
    disabled={isSubmitting}
  />
        <button
          onClick={() => {
            console.log("Submitted:", text);
            handleAnalysis();
          }}
          className="px-5 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Submit
        </button>
        <div className="text-black bg-black/40 text-sm p-4 rounded border border-white/10 max-h-64 overflow-y-auto w-full">
        <p>{analysis}</p>
        </div>
      </LargePopup>
          </div>
          
          {done && (
            <div className="mt-4 flex flex-col items-center gap-3">
              <button
                onClick={downloadPDF}
                className="bg-green-500 hover:bg-green-600 text-gray-100 bg-opacity-80 px-4 py-2 rounded-md"
              >
                Download Patient Summary PDF
              </button>
              <button
                onClick={fetchSummary}
                className="bg-orange-500 hover:bg-orange-600 text-gray-100 px-4 py-2 rounded-md"
              >
                Show Conversation Summary
              </button>
              <label className="text-sm mt-4">
                📄 Upload Document for Q/A:
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
        {/* <Popup isOpen={isPopupOpen} onClose={closePopup}>
        <h2 className="text-xl font-bold text-black mb-4">Hello from the Popup!</h2>
        <p className="text-black">Press <kbd>Escape</kbd> to close this popup.</p>
      </Popup> */}
        <Popup isOpen={isPopupOpen} onClose={closePopup}>
        <div className="flex gap-2 mt-4">
  <input
    type="text"
    value={followUpQ}
    onChange={(e) => setFollowUpQ(e.target.value)}
    onKeyDown={(e) => e.key === "Enter" && handleFollowUp()}
    className="flex-1 px-4 py-2 text-black border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
    placeholder="Ask a follow-up question..."
    disabled={isSubmitting}
  />
  <button
  onClick={() => {
    setIsPopupOpen(false);
    handleFollowUp();
  }}
    disabled={isSubmitting}
    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
  >
    Send
  </button>
</div>
      </Popup>
      </div>
    </div>
  );
}

export default PatientChat;
