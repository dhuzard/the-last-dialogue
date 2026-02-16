'use client';

import { useState, useEffect, useRef } from 'react';

export default function Home() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('Idle');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Mock initial manuscript for scaffolding visualization
  useEffect(() => {
    setMessages([
      "The system initialized.",
      "Protocols active.",
      "Waiting for Director Input..."
    ]);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const command = input;
    setInput('');
    setMessages(prev => [...prev, `> ${command}`]);
    setStatus('Processing...');

    // TODO: Connect to backend API
    // await fetch('/api/turn', { method: 'POST', body: JSON.stringify({ human_intent: command }) });

    setTimeout(() => {
      setMessages(prev => [...prev, "System: [Simulated AI Response] The narrative shifts..."]);
      setStatus('Idle');
    }, 1000);
  };

  return (
    <main className="flex h-screen flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Header */}
      <header className="p-4 border-b border-gray-800 flex justify-between items-center">
        <h1 className="text-xl font-bold tracking-wider text-green-500">THE LAST DIALOGUE</h1>
        <div className="text-xs text-gray-500">{status}</div>
      </header>

      {/* The Book (Manuscript View) */}
      <div className="flex-1 overflow-y-auto p-8 space-y-4 scroll-smooth" ref={scrollRef}>
        <div className="max-w-3xl mx-auto bg-gray-800 p-8 rounded shadow-lg min-h-full">
          {messages.map((msg, idx) => (
            <p key={idx} className={msg.startsWith('>') ? "text-green-400 font-mono mb-2" : "text-gray-300 mb-4 leading-relaxed"}>
              {msg}
            </p>
          ))}
        </div>
      </div>

      {/* Terminal Input */}
      <div className="h-48 bg-black border-t border-gray-800 p-6 flex flex-col">
        <div className="text-xs text-green-700 mb-2 uppercase tracking-widest">Director Input</div>
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-transparent text-green-500 font-mono text-lg focus:outline-none resize-none p-2"
            placeholder="Enter your intent..."
            spellCheck={false}
            autoFocus
          />
          <div className="flex justify-end mt-2">
            <button
              type="submit"
              className="bg-green-900 hover:bg-green-800 text-green-100 px-6 py-2 rounded text-sm uppercase tracking-wide transition-colors"
            >
              Generate
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
