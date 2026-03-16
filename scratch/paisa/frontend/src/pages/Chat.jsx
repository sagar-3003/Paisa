import React, { useState } from 'react';
import axios from 'axios';
import EntryCard from '../components/EntryCard';

function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'ai',
      text: 'Hello! I am Paisa, your AI Accountant. You can text me details of sales, purchases, or expenses, or upload an invoice, and I will parse it for you.',
    }
  ]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMsg = { id: Date.now(), role: 'user', text: input };
    setMessages([...messages, newMsg]);
    setInput('');
    
    // Add loading state message
    const loadingId = Date.now() + 1;
    setMessages(prev => [...prev, { id: loadingId, role: 'ai', text: 'Thinking...' }]);
    
    try {
      const response = await axios.post('/api/chat', { message: input });
      
      setMessages(prev => prev.map(msg => 
        msg.id === loadingId 
          ? { id: loadingId, role: 'ai', text: response.data.answer || null, parsedData: response.data.intent !== 'query' ? response.data : null }
          : msg
      ));
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => prev.map(msg => 
        msg.id === loadingId 
          ? { id: loadingId, role: 'ai', text: 'Oops! I had trouble connecting to my brain. Please try again later. Make sure the backend is running.' }
          : msg
      ));
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto space-y-6 p-4 rounded-xl">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] rounded-2xl p-4 shadow-sm ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border text-slate-800 rounded-bl-none'}`}>
              {msg.text && <p className="leading-relaxed">{msg.text}</p>}
              {msg.parsedData && <EntryCard data={msg.parsedData} />}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 bg-white border rounded-full shadow-sm p-2 flex items-center relative">
        <label className="p-3 text-slate-400 hover:text-indigo-600 transition-colors rounded-full hover:bg-slate-50 cursor-pointer">
          <input 
            type="file" 
            className="hidden" 
            accept="image/*,.pdf" 
            onChange={async (e) => {
              if (!e.target.files || e.target.files.length === 0) return;
              const file = e.target.files[0];
              
              const newMsg = { id: Date.now(), role: 'user', text: `Uploaded invoice: ${file.name}` };
              setMessages([...messages, newMsg]);
              
              const loadingId = Date.now() + 1;
              setMessages(prev => [...prev, { id: loadingId, role: 'ai', text: 'Scanning document structure...' }]);
              
              const formData = new FormData();
              formData.append('file', file);
              
              try {
                const response = await axios.post('/api/scan-invoice', formData, {
                  headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                setMessages(prev => prev.map(msg => 
                  msg.id === loadingId 
                    ? { 
                        id: loadingId, 
                        role: 'ai', 
                        text: response.data.error ? response.data.error : null, 
                        parsedData: response.data.error ? null : response.data 
                      }
                    : msg
                ));
              } catch (error) {
                console.error("Scan error:", error);
                setMessages(prev => prev.map(msg => 
                  msg.id === loadingId 
                    ? { id: loadingId, role: 'ai', text: 'Sorry, I failed to scan the document.' }
                    : msg
                ));
              }
            }} 
          />
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        </label>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a transaction or upload an invoice..." 
          className="flex-1 outline-none font-medium px-4 text-slate-700 placeholder-slate-400 bg-transparent"
        />
        <button 
          onClick={handleSend}
          className="bg-indigo-600 text-white p-3 rounded-full hover:bg-indigo-700 hover:scale-105 transition-all shadow-md flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
            <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default Chat;
