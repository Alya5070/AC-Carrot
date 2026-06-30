"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useGuild } from "../context/GuildContext";
import { apiFetch } from "../lib/api";

export function OverviewChart() {
  const { selectedGuildId, loading: guildLoading } = useGuild();
  const [data, setData] = useState<any[]>([]);
  const [period, setPeriod] = useState<"week" | "month" | "year">("month");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Wait for guild context to finish loading, and require a real guild ID.
    if (guildLoading || !selectedGuildId || selectedGuildId === "0") {
      setLoading(false);
      setData([]);
      return;
    }

    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/analytics?period=${period}`)
      .then(res => res.json())
      .then(raw => {
        // Support both { data: [...] } and a bare array response shape
        const items: any[] = Array.isArray(raw) ? raw : (raw.data || []);
        const formattedData = items.map((item: any) => {
          const date = new Date(item.date);
          return {
            ...item,
            displayDate: period === "year"
              ? date.toLocaleDateString('en-US', { month: 'short' })
              : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          };
        });
        setData(formattedData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching analytics:", err);
        setLoading(false);
      });
  }, [selectedGuildId, guildLoading, period]);

  return (
    <div className="glass-panel border border-white/5 rounded-xl p-6 h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Server Analytics</h2>
          <p className="text-sm text-gray-400">Warnings and Paid Requests over time</p>
        </div>
        
        <div className="flex items-center bg-surface-darker rounded-lg p-1 border border-teal-900/30">
          {(["week", "month", "year"] as const).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-1.5 rounded-md text-xs font-medium capitalize transition-all ${
                period === p 
                  ? "bg-teal-500/20 text-teal-300 shadow-sm" 
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 min-h-0 w-full relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-teal-500 animate-pulse font-mono text-sm">Loading graph...</span>
          </div>
        ) : data.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-gray-500 text-sm">No data available for this period.</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorWarnings" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
                axisLine={false}
                minTickGap={20}
                tickFormatter={(value) => {
                  try {
                    const date = new Date(value);
                    return period === "year"
                      ? date.toLocaleDateString('en-US', { month: 'short' })
                      : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  } catch (e) {
                    return value;
                  }
                }}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#111827', 
                  border: '1px solid rgba(20, 184, 166, 0.2)',
                  borderRadius: '0.5rem',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                }}
                itemStyle={{ fontSize: '14px', fontWeight: 500 }}
                labelStyle={{ color: '#9ca3af', marginBottom: '4px', fontSize: '12px' }}
                labelFormatter={(value) => {
                  try {
                    const date = new Date(value);
                    return period === "year"
                      ? date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
                      : date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                  } catch (e) {
                    return value;
                  }
                }}
              />
              <Area 
                type="monotone" 
                dataKey="warnings" 
                name="Verbal Warnings"
                stroke="#f43f5e" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorWarnings)" 
              />
              <Area 
                type="monotone" 
                dataKey="requests" 
                name="Paid Requests"
                stroke="#14b8a6" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorRequests)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
