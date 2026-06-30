"use client";

import { useEffect, useState } from "react";
import { Activity, ShieldAlert, CreditCard, Bell, X } from "lucide-react";
import Link from "next/link";
import { useGuild } from "../../context/GuildContext";
import { OverviewChart } from "../../components/OverviewChart";
import { apiFetch } from "../../lib/api";

type Warning = {
  id: number;
  user_id: number;
  user_name: string;
  user_avatar: string | null;
  warned_at: string;
  reason: string | null;
  staff_name: string;
};

type PaidRequest = {
  request_id: number;
  user_id: number;
  user_name: string;
  user_avatar: string | null;
  budget: string;
  status: string;
  created_at: string;
};

export default function OverviewPage() {
  const [stats, setStats] = useState({
    bot_status: "Loading...",
    ping: "--",
    pending_requests: 0,
    verbals_this_week: 0,
    verbals_trend: "--",
    active_reminders: 0
  });

  const [recentWarnings, setRecentWarnings] = useState<Warning[]>([]);
  const [recentRequests, setRecentRequests] = useState<PaidRequest[]>([]);

  const { selectedGuildId } = useGuild();

  useEffect(() => {
    if (!selectedGuildId || selectedGuildId === "0") {
      setStats({
        bot_status: "Offline",
        ping: "0ms",
        pending_requests: 0,
        verbals_this_week: 0,
        verbals_trend: "--",
        active_reminders: 0
      });
      setRecentWarnings([]);
      setRecentRequests([]);
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Fetch Stats
    apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/stats`)
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error("Error fetching stats:", err));

    // Fetch Recent Warnings (limit 5)
    apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/warnings?limit=5`)
      .then((res) => res.json())
      .then((data) => setRecentWarnings(data.warnings || []))
      .catch((err) => console.error("Error fetching warnings:", err));

    // Fetch Recent Requests (limit 5)
    apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/paid-requests?limit=5`)
      .then((res) => res.json())
      .then((data) => setRecentRequests(data.requests || []))
      .catch((err) => console.error("Error fetching requests:", err));

  }, [selectedGuildId]);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          Overview Dashboard
        </h1>
        <p className="text-gray-400 mt-1">High-level statistics and recent activity for the AC Carrot bot.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-6 rounded-xl border border-teal-900/30">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-400" /> Bot Status
          </div>
          <div className={`text-3xl font-bold ${stats.bot_status === 'Online' ? 'text-teal-400' : 'text-red-400'}`}>{stats.bot_status}</div>
          <div className="text-teal-400/70 text-sm mt-2">Ping: {stats.ping}</div>
        </div>

        <div className="glass-panel p-6 rounded-xl border border-teal-900/30">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-teal-400" /> Pending Requests
          </div>
          <div className="text-3xl font-bold text-white">{stats.pending_requests}</div>
          <div className="text-gray-500 text-sm mt-2">Total System Pending</div>
        </div>

        <div className="glass-panel p-6 rounded-xl border border-teal-900/30">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400" /> Verbals This Week
          </div>
          <div className="text-3xl font-bold text-white">{stats.verbals_this_week}</div>
          <div className="text-red-400 text-sm mt-2 font-medium">{stats.verbals_trend}</div>
        </div>

        <div className="glass-panel p-6 rounded-xl border border-teal-900/30">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
            <Bell className="w-4 h-4 text-teal-400" /> Active Reminders
          </div>
          <div className="text-3xl font-bold text-white">{stats.active_reminders}</div>
          <div className="text-gray-500 text-sm mt-2">System wide</div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="mb-8">
        <OverviewChart />
      </div>



      {/* Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Recent Warnings Snapshot */}
        <div className="glass-panel rounded-xl border border-teal-900/30 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-teal-900/30 flex justify-between items-center bg-surface-dark/50">
            <h2 className="text-base font-bold text-white">Recent Verbal Warnings</h2>
            <Link href="/logs/warnings" className="text-teal-400 hover:text-teal-300 text-xs font-medium px-3 py-1.5 bg-teal-500/10 hover:bg-teal-500/20 rounded transition-colors">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-surface-dark/30 border-b border-teal-900/20 text-teal-400/70 font-medium text-xs">
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-teal-900/10">
                {recentWarnings.length === 0 ? (
                  <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-500">No warnings found.</td></tr>
                ) : (
                  recentWarnings.map(w => (
                    <tr key={w.id} className="hover:bg-teal-900/5 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {w.user_avatar ? (
                            <img src={w.user_avatar} alt="" className="w-6 h-6 rounded-full" />
                          ) : (
                            <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-bold text-gray-400">
                              {w.user_name.charAt(0).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <div className="font-medium text-gray-200 text-xs truncate max-w-[100px]">{w.user_name}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="truncate max-w-[150px] text-gray-400 text-xs">
                          {w.reason || "No reason"}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {new Date(w.warned_at + "Z").toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Paid Requests Snapshot */}
        <div className="glass-panel rounded-xl border border-teal-900/30 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-teal-900/30 flex justify-between items-center bg-surface-dark/50">
            <h2 className="text-base font-bold text-white">Latest Paid Requests</h2>
            <Link href="#" className="text-teal-400 hover:text-teal-300 text-xs font-medium px-3 py-1.5 bg-teal-500/10 hover:bg-teal-500/20 rounded transition-colors">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-surface-dark/30 border-b border-teal-900/20 text-teal-400/70 font-medium text-xs">
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Budget</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-teal-900/10">
                {recentRequests.length === 0 ? (
                  <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">No requests found.</td></tr>
                ) : (
                  recentRequests.map(r => (
                    <tr key={r.request_id} className="hover:bg-teal-900/5 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {r.user_avatar ? (
                            <img src={r.user_avatar} alt="" className="w-6 h-6 rounded-full" />
                          ) : (
                            <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-bold text-gray-400">
                              {r.user_name.charAt(0).toUpperCase()}
                            </div>
                          )}
                          <div className="font-medium text-gray-200 text-xs truncate max-w-[100px]">{r.user_name}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-300 text-xs font-mono">{r.budget}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          r.status === 'pending' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 
                          r.status === 'approved' ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 
                          'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}>
                          {r.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {new Date(r.created_at + "Z").toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
