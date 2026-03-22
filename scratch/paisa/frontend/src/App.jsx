import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import TallyLedger from './pages/TallyLedger';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="bg-white border-b border-slate-200 py-3 px-6 fixed top-0 w-full z-10 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-indigo-600 tracking-tight">Paisa</h1>
            <span className="text-sm text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-full">AI Accountant</span>
          </div>
          <nav className="flex items-center gap-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              Chat
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/ledger"
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              Tally Ledger
            </NavLink>
          </nav>
        </header>

        <main className="flex-1 mt-14">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/ledger" element={<TallyLedger />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
