import React from 'react';
import Chat from './pages/Chat';
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 py-4 px-6 fixed top-0 w-full z-10 flex items-center shadow-sm">
        <h1 className="text-xl font-bold text-indigo-600 tracking-tight">Paisa</h1>
        <span className="ml-2 text-sm text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-full">AI Accountant</span>
      </header>
      <main className="flex-1 mt-16 pb-0">
        <Chat />
      </main>
    </div>
  );
}

export default App;
