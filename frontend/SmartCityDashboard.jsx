import React, { useState, useEffect } from 'react';

// --- Premium UI Components ---
const GlassCard = ({ children, className = '', title, icon }) => (
  <div className={`relative overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.5)] transition-all duration-300 hover:border-slate-600/50 ${className}`}>
    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-50" />
    <div className="flex items-center gap-3 mb-5 border-b border-slate-700/50 pb-3">
      <span className="text-cyan-400 text-xl">{icon}</span>
      <h2 className="text-sm font-bold tracking-widest text-slate-300 uppercase font-mono">{title}</h2>
    </div>
    {children}
  </div>
);

const StatusBadge = ({ status }) => {
  const styles = {
    COMMITTED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]',
    PREPARED: 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.2)] animate-pulse',
    ABORTED: 'bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_10px_rgba(225,29,72,0.2)]',
    CRITICAL: 'bg-rose-600 border-rose-400 text-white shadow-[0_0_15px_rgba(225,29,72,0.6)] animate-pulse',
    HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    MEDIUM: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    LOW: 'bg-slate-800 text-slate-400 border-slate-600',
  };

  // Default to LOW if status isn't matched
  const appliedStyle = styles[status] || styles.LOW;

  return (
    <span className={`px-3 py-1 text-[10px] font-black tracking-wider rounded-md border uppercase ${appliedStyle}`}>
      {status}
    </span>
  );
};

export default function SmartCityDashboard() {
  const [isConnected, setIsConnected] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  const [systemState, setSystemState] = useState({
    lamport: 0,
    events: [
    ],
    subscribers: {
    },
    transactions: [
    ]
  });

  // Mock Engine Simulation Loop
  useEffect(() => {
    if (!useMockData) return;

    const interval = setInterval(() => {
      setSystemState(prev => {
        const nextClock = prev.lamport + Math.floor(Math.random() * 5) + 1;

        const mockEventsList = [
          { s: 'weather-sensor', d: 'Heavy rain expected — possible waterlogging', v: 'MEDIUM' },
          { s: 'traffic-sensor', d: 'Major accident on Highway 5 — 3 vehicles involved', v: 'HIGH' },
          { s: 'pollution-sensor', d: 'Chemical leak detected near factory district', v: 'CRITICAL' },
          { s: 'traffic-sensor', d: 'Rush hour congestion — average speed 12 km/h', v: 'LOW' },
          { s: 'weather-sensor', d: 'Temperature hits 47°C — extreme heat advisory', v: 'HIGH' }
        ];
        const randomE = mockEventsList[Math.floor(Math.random() * mockEventsList.length)];

        const newEvent = {
          id: Date.now(),
          time: new Date().toLocaleTimeString('en-US', { hour12: false }),
          source: randomE.s,
          data: randomE.d,
          severity: randomE.v
        };

        // Progress transactions
        let txList = prev.transactions.map(tx =>
          tx.status === 'PREPARED' && Math.random() > 0.4 ? { ...tx, status: 'COMMITTED' } : tx
        );

        // Generate new transactions for HIGH/CRITICAL events
        if (newEvent.severity === 'CRITICAL' || newEvent.severity === 'HIGH') {
          const affectedTopic = newEvent.source.split('-')[0];
          const participants = prev.subscribers[affectedTopic] || ['system_monitor'];
          txList.unshift({
            tx_id: `TX-${Math.random().toString(16).substr(2, 4).toUpperCase()}`,
            status: 'PREPARED',
            nodes: participants
          });
        }

        return {
          lamport: nextClock,
          events: [newEvent, ...prev.events.slice(0, 5)], // Keep last 6 events
          subscribers: prev.subscribers,
          transactions: txList.slice(0, 4) // Keep last 4 transactions
        };
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [useMockData]);

  // Real production polling engine (Connects to Python Backend Bridge)
  useEffect(() => {
    if (useMockData) return;

    const fetchData = async () => {
      try {
        const response = await fetch(
          'http://16.171.16.165:5000/api/status',
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log('BROKER DATA:', data);

        setSystemState({
          lamport: data.lamport || 0,
          events: data.events || [],
          subscribers: data.subscribers || {},
          transactions: data.transactions || []
        });

        setIsConnected(true);
      } catch (err) {
        console.error('Dashboard Fetch Error:', err);
        setIsConnected(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [useMockData]);

  return (
    <div className="min-h-screen bg-[#050B14] text-slate-200 font-sans p-4 md:p-8 selection:bg-cyan-500/30">

      {/* Background Ambience / Cyber Glow */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-900/20 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/10 blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto">

        {/* Header HUD */}
        <header className="flex flex-col md:flex-row items-start md:items-end justify-between border-b border-cyan-900/50 pb-6 mb-8 gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="relative flex h-4 w-4">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-cyan-400' : 'bg-rose-500'}`}></span>
                <span className={`relative inline-flex rounded-full h-4 w-4 ${isConnected ? 'bg-cyan-500' : 'bg-rose-600'}`}></span>
              </span>
              <h1 className="text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 uppercase drop-shadow-sm">
                Smart City Nerve Center
              </h1>
            </div>
            <p className="text-sm font-mono text-cyan-500/70 ml-7 tracking-widest uppercase">Distributed Event Notification System v2.0</p>
          </div>

          <button
            onClick={() => setUseMockData(!useMockData)}
            className={`font-mono text-xs px-4 py-2 rounded-lg border transition-all duration-300 hover:scale-105 ${useMockData
              ? 'bg-purple-500/10 text-purple-400 border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]'
              : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
              }`}
          >
            {useMockData ? '⚡ SIMULATION OVERRIDE ACTIVE' : '🌐 LIVE BROKER UPLINK'}
          </button>
        </header>

        {/* 4-Panel Grid */}
        <main className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Panel 1: Data Stream */}
          <GlassCard title="Live Pub-Sub Stream" icon="📡">
            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {systemState.events.length === 0 ? (
                <div className="text-center py-10 text-slate-500 font-mono">
                  Waiting for broker events...
                </div>
              ) : systemState.events.map((ev) => (
                <div key={ev.id} className="group flex flex-col gap-1 bg-black/40 p-3 rounded-lg border border-slate-800 hover:border-cyan-500/30 transition-colors">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-cyan-500 font-mono text-xs tracking-wider">[{ev.time}]</span>
                    <StatusBadge status={ev.severity} />
                  </div>
                  <div className="flex gap-3 items-start">
                    <span className="text-[10px] text-slate-500 uppercase font-bold w-24 shrink-0 mt-0.5">{ev.source}</span>
                    <span className="text-sm text-slate-200 leading-snug">{ev.data}</span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Panel 2: Lamport Clock */}
          <GlassCard title="Global Logical Time" icon="⏱️" className="flex flex-col">
            <p className="text-xs text-slate-400 mb-auto leading-relaxed">
              Causality is maintained across distributed city nodes using Lamport Timestamps, bypassing hardware NTP limitations.
            </p>
            <div className="relative group mx-auto my-8">
              {/* Glowing ring effect */}
              <div className="absolute -inset-2 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-full blur-md opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-200" />
              <div className="relative flex flex-col items-center justify-center bg-black w-56 h-56 rounded-full border border-cyan-900/50 shadow-2xl">
                <span className="text-[10px] text-cyan-500 font-mono tracking-widest mb-1 uppercase">Lamport Val</span>
                <span className="text-7xl font-black text-white tracking-tighter drop-shadow-[0_0_15px_rgba(6,182,212,0.8)]">
                  {systemState.lamport}
                </span>
                <span className="text-[9px] font-mono text-emerald-500 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/60 mt-3 absolute bottom-6">
                  MAX(Local, Recv) + 1
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Panel 3: Mutex Registry */}
          <GlassCard title="Active Subscriptions (Mutex)" icon="🔐">
            <div className="grid gap-3">
              {Object.entries(systemState.subscribers).map(([topic, consumers]) => (
                <div key={topic} className="flex justify-between items-center p-4 bg-black/40 rounded-lg border border-slate-800 hover:bg-slate-900/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-[pulse_1.5s_ease-in-out_infinite]" />
                    <span className="text-sm font-mono text-emerald-400 uppercase tracking-widest">{topic}</span>
                  </div>
                  <div className="flex gap-2 flex-wrap justify-end">
                    {consumers.map((sub, i) => (
                      <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700 uppercase shadow-sm">
                        {sub.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Panel 4: Transactions */}
          <GlassCard title="2PC-Lite Transactions" icon="⚡">
            <div className="space-y-3">
              {systemState.transactions.length > 0 ? (
                systemState.transactions.map((tx) => (
                  <div key={tx.tx_id} className="flex flex-col gap-2 p-3 bg-black/40 rounded-lg border border-slate-800 hover:border-slate-600 transition-colors">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-mono text-slate-200 font-bold tracking-wider">{tx.tx_id}</span>
                      <StatusBadge status={tx.status} />
                    </div>
                    <div className="flex items-center gap-2 bg-slate-950/50 p-2 rounded">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold shrink-0">Awaiting ACK:</span>
                      <span className="text-xs text-cyan-400 font-mono truncate">
                        {(tx.participants || tx.nodes || []).join(' + ')}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-10 text-slate-600 text-sm font-mono border border-dashed border-slate-800 rounded-lg bg-black/20">
                  <span className="text-2xl mb-2 opacity-50">⏸️</span>
                  <span>No active atomic transactions</span>
                </div>
              )}
            </div>
          </GlassCard>

        </main>

        {/* Footer */}
        <footer className="mt-8 text-center text-[10px] font-mono text-cyan-900/60 uppercase tracking-widest border-t border-cyan-950 pt-4">
          Core Engine: Python TCP Broker • UI Render: React.js • Secure Distributed System Buffer
        </footer>
      </div>
    </div>
  );
}