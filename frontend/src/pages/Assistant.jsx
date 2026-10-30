import { useState } from "react";
import { postChat } from "../lib/api";
import { Bot, User, Send } from "lucide-react";

export default function Assistant() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! I'm your AI Sales Assistant. Ask me anything about your e-commerce data — revenue trends, top products, customer behaviour, or strategic recommendations." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const res = await postChat(msg);
      setMessages(m => [...m, { role: "bot", text: res.response }]);
    } catch {
      setMessages(m => [...m, { role: "bot", text: "⚠️ Could not reach the AI backend. Please ensure the FastAPI server is running on port 8000." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <h2>AI Sales Assistant</h2>
        <p>Privacy-preserving local AI assistant with deterministic fallback</p>
      </div>

      <div className="card" style={{display:"flex",flexDirection:"column",height:"65vh"}}>
        <div style={{flex:1,overflowY:"auto",display:"flex",flexDirection:"column",gap:12,padding:"8px 0",marginBottom:16}}>
          {messages.map((m,i) => (
            <div key={i} style={{display:"flex",gap:10,alignItems:"flex-start",flexDirection:m.role==="user"?"row-reverse":"row"}}>
              <div style={{
                width:32,height:32,borderRadius:"50%",flexShrink:0,display:"flex",
                alignItems:"center",justifyContent:"center",
                background: m.role==="user"?"var(--accent)":"var(--surface2)",
                border:"1px solid var(--border)"
              }}>
                {m.role==="user" ? <User size={15}/> : <Bot size={15} color="#6366f1"/>}
              </div>
              <div className={`chat-bubble ${m.role}`} style={{whiteSpace:"pre-wrap"}}>{m.text}</div>
            </div>
          ))}
          {loading && (
            <div style={{display:"flex",gap:10,alignItems:"flex-start"}}>
              <div style={{width:32,height:32,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",background:"var(--surface2)",border:"1px solid var(--border)"}}>
                <Bot size={15} color="#6366f1"/>
              </div>
              <div className="chat-bubble bot" style={{display:"flex",gap:6,alignItems:"center"}}>
                <span className="spinner" style={{width:16,height:16,borderWidth:2,marginRight:0}}/>
                Thinking...
              </div>
            </div>
          )}
        </div>

        <div className="chat-input-row">
          <input
            className="input"
            placeholder="Ask about revenue, top products, customer segments..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
          />
          <button className="btn btn-primary" onClick={handleSend} disabled={loading}>
            <Send size={15}/> Send
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Example Questions</div>
        <div style={{display:"flex",flexWrap:"wrap",gap:8,marginTop:4}}>
          {[
            "What is our total revenue?",
            "Who are our top 5 customers?",
            "Which products sell the most?",
            "What is the repeat customer rate?",
            "Which country generates most revenue?",
            "What is the average order value?",
          ].map(q => (
            <button key={q} className="btn btn-ghost" style={{fontSize:"0.76rem",padding:"5px 12px"}}
              onClick={() => { setInput(q); }}>
              {q}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
