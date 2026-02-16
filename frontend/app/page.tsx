'use client';

import { useState, useEffect, useRef } from 'react';

type GameState = {
  thread_id?: string;
  active_player: string;
  status: string;
};

export default function Home() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [gameState, setGameState] = useState<GameState>({
    active_player: "Initializing...",
    status: "Idle"
  });
  const scrollRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  // Initialize Session
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    async function startSession() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/start_session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ player_1_name: "Persona A", player_2_name: "Persona B" })
        });
        const data = await res.json();
        setGameState({
          thread_id: data.thread_id,
          active_player: "Persona A",
          status: "Waiting for Input"
        });
        setMessages([
          "System Initialized.",
          "Protocol: The Last Dialogue.",
          `Session ID: ${data.thread_id}`,
          "Begin."
        ]);
      } catch (err) {
        console.error(err);
        setMessages(["Error connecting to system backend."]);
      }
    }

    startSession();
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !gameState.thread_id) return;

    const command = input;
    setInput('');
    setMessages(prev => [...prev, `\n> [Director]: ${command}`]);
    setGameState(prev => ({ ...prev, status: "Processing (Researching & Writing)..." }));

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: gameState.thread_id,
          human_intent: command
        })
      });

      const data = await res.json();

      // Append new manuscript content
      if (data.manuscript) {
        setMessages(prev => [...prev, data.manuscript]);
      }

      setGameState({
        thread_id: data.thread_id,
        active_player: data.active_player,
        status: `Waiting for ${data.active_player} Input`
      });

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, "[System Error]: Transmission failed."]);
      setGameState(prev => ({ ...prev, status: "Error" }));
    }
  };

  return (
    <main className="flex h-screen flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Header */}
      <header className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-950">
        <h1 className="text-xl font-bold tracking-wider text-green-500">THE LAST DIALOGUE</h1>
        <div className="flex gap-4 text-xs font-mono">
          <span className="text-blue-400">ACTIVE: {gameState.active_player}</span>
          <span className="text-gray-500">[{gameState.status}]</span>
        </div>
      </header>

      {/* The Book (Manuscript View) */}
      <div className="flex-1 overflow-y-auto p-8 space-y-4 scroll-smooth" ref={scrollRef}>
        <div className="max-w-3xl mx-auto bg-gray-800 p-12 rounded shadow-2xl min-h-full border border-gray-700">
          {messages.map((msg, idx) => {
            // Simple formatting for creating visual distinction
            const isCommand = msg.startsWith('\n> [Director]');
            return (
              <div key={idx} className={isCommand ? "text-green-600 font-mono text-sm mb-6 border-l-2 border-green-800 pl-4 py-2" : "text-gray-300 mb-6 leading-loose font-serif text-lg whitespace-pre-wrap"}>
                {msg}
              </div>
            );
          })}
        </div>
      </div>

      {/* Terminal Input */}
      <div className="h-48 bg-black border-t border-gray-800 p-6 flex flex-col shadow-inner">
        <div className="text-xs text-green-700 mb-2 uppercase tracking-widest font-bold">
          Director Interface // {gameState.active_player}
        </div>
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={gameState.status.startsWith("Processing")}
            className="flex-1 bg-transparent text-green-500 font-mono text-lg focus:outline-none resize-none p-2 disabled:opacity-50"
            placeholder={gameState.status.startsWith("Processing") ? "System processing..." : "Enter your high-level intent..."}
            spellCheck={false}
            autoFocus
          />
          <div className="flex justify-end mt-2">
            <button
              type="submit"
              disabled={gameState.status.startsWith("Processing") || !input.trim()}
              className="bg-green-900 hover:bg-green-800 disabled:bg-gray-800 disabled:text-gray-600 text-green-100 px-6 py-2 rounded text-sm uppercase tracking-wide transition-colors font-bold"
            >
              Generate Protocol
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
