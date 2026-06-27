"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Search, Trash2, RefreshCw, Clock, MessageSquare, ExternalLink } from "lucide-react";
import { useGuild } from "../../../context/GuildContext";

type Warning = {
  id: number;
  user_id: number;
  user_name: string;
  user_avatar: string | null;
  warned_at: string;
  channel_id: number;
  message_id: number;
  message_content: string | null;
  staff_id: number;
  staff_name: string;
  staff_avatar: string | null;
  reason: string | null;
  post_created_at: string | null;
};

export default function WarningsPage() {
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWarning, setSelectedWarning] = useState<Warning | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { selectedGuildId } = useGuild();

  const fetchWarnings = () => {
    if (!selectedGuildId || selectedGuildId === "0") return;
    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/guilds/${selectedGuildId}/warnings`)
      .then((res) => res.json())
      .then((data) => {
        setWarnings(data.warnings || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching warnings:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (selectedGuildId && selectedGuildId !== "0") {
      fetchWarnings();
    }
  }, [selectedGuildId]);

  const filteredWarnings = warnings.filter((w) => {
    const query = searchQuery.toLowerCase();
    return (
      (w.user_name || "").toLowerCase().includes(query) ||
      (w.user_id || "").toString().includes(query) ||
      (w.reason || "").toLowerCase().includes(query) ||
      (w.staff_name || "").toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <ShieldAlert className="text-teal-400 w-8 h-8" />
            Warning Logs
          </h1>
          <p className="text-gray-400 mt-1">Review and manage verbal warnings issued by staff.</p>
        </div>
        
        <div className="flex items-center gap-3 relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <Search className="w-4 h-4" />
          </div>
          <input 
            type="text" 
            placeholder="Search users or reasons..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 bg-surface-dark border border-teal-900/40 rounded-lg text-sm text-white focus:outline-none focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 w-full md:w-64 transition-all"
          />
          <button 
            onClick={fetchWarnings}
            disabled={loading}
            className="bg-surface-dark border border-teal-900/40 p-2 rounded-lg text-gray-400 hover:text-white hover:border-teal-500/50 transition-colors disabled:opacity-50"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-500' : ''}`} />
          </button>
        </div>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-surface-dark/80 border-b border-teal-900/30 text-teal-400/80 font-medium">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Reason</th>
                <th className="px-6 py-4">Issued By</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-teal-900/20 bg-surface-dark/40">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    <div className="animate-pulse flex flex-col items-center gap-2">
                      <div className="w-8 h-8 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
                      Loading logs...
                    </div>
                  </td>
                </tr>
              ) : filteredWarnings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No warnings found matching your search.
                  </td>
                </tr>
              ) : (
                filteredWarnings.map((w) => (
                  <tr key={w.id} className="hover:bg-teal-900/10 transition-colors group">
                    <td className="px-6 py-4 text-gray-400 font-mono">#{w.id}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {w.user_avatar ? (
                          <img src={w.user_avatar} alt="" className="w-8 h-8 rounded-full bg-gray-800" />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 text-xs font-bold">
                            {w.user_name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-medium text-gray-200">{w.user_name}</div>
                          <div className="text-xs text-gray-500 font-mono">{w.user_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-xs truncate text-gray-300">
                        {w.reason || "No reason provided"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {w.staff_avatar ? (
                          <img src={w.staff_avatar} alt="" className="w-6 h-6 rounded-full bg-gray-800" />
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 text-xs font-bold">
                            {w.staff_name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <span className="text-gray-300 text-sm">{w.staff_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-400 whitespace-nowrap">
                      {new Date(w.warned_at + "Z").toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => setSelectedWarning(w)}
                        className="text-teal-400 hover:text-teal-300 bg-teal-500/10 hover:bg-teal-500/20 px-3 py-1.5 rounded text-xs font-medium transition-colors"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm" 
            onClick={() => setSelectedWarning(null)}
          />
          <div className="relative w-full max-w-2xl max-h-[85vh] flex flex-col bg-surface-card border border-teal-900/40 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-surface-darker/50">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-teal-400" />
                Warning Details <span className="text-gray-500 font-mono text-sm ml-2">#{selectedWarning.id}</span>
              </h2>
              <button 
                onClick={() => setSelectedWarning(null)}
                className="text-gray-400 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors"
              >
                ✕
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 text-sm">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-1">
                  <div className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-2">Original Author</div>
                  <div className="flex items-center gap-3 bg-surface-darker p-3 rounded-lg border border-white/5">
                    {selectedWarning.user_avatar ? (
                      <img src={selectedWarning.user_avatar} alt="" className="w-10 h-10 rounded-full" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center font-bold">
                        {selectedWarning.user_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <div className="font-medium text-white">{selectedWarning.user_name}</div>
                      <div className="text-gray-500 font-mono text-xs">{selectedWarning.user_id}</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-2">Issued By Staff</div>
                  <div className="flex items-center gap-3 bg-surface-darker p-3 rounded-lg border border-white/5">
                    {selectedWarning.staff_avatar ? (
                      <img src={selectedWarning.staff_avatar} alt="" className="w-10 h-10 rounded-full" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center font-bold">
                        {selectedWarning.staff_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <div className="font-medium text-white">{selectedWarning.staff_name}</div>
                      <div className="text-gray-500 font-mono text-xs">{selectedWarning.staff_id}</div>
                    </div>
                  </div>
                </div>
              </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-surface-darker p-4 rounded-lg border border-white/5 space-y-1">
                    <div className="text-gray-500 text-xs flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> Post Created At</div>
                    <div className="text-gray-300">{selectedWarning.post_created_at ? new Date(selectedWarning.post_created_at).toLocaleString() : "Unknown"}</div>
                  </div>
                  <div className="bg-surface-darker p-4 rounded-lg border border-white/5 space-y-1">
                    <div className="text-gray-500 text-xs flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> Warning Issued</div>
                    <div className="text-teal-300 font-medium">{new Date(selectedWarning.warned_at + "Z").toLocaleString()}</div>
                  </div>
                  <div className="bg-surface-darker p-4 rounded-lg border border-white/5 space-y-1">
                    <div className="text-gray-500 text-xs flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5" /> Channel ID</div>
                    <div className="text-gray-300 font-mono text-xs mt-1">{selectedWarning.channel_id}</div>
                  </div>
                </div>

              <div>
                <div className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-2">Rejection Reason</div>
                <div className="bg-surface-darker p-4 rounded-lg border border-teal-900/40 text-gray-300 whitespace-pre-wrap leading-relaxed shadow-inner">
                  {selectedWarning.reason || "No reason recorded."}
                </div>
              </div>

              <div>
                <div className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-2 flex justify-between items-center">
                  <span>Original Post Content</span>
                  <a href={`https://discord.com/channels/0/${selectedWarning.channel_id}`} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-teal-400 hover:text-teal-300 transition-colors">
                    <ExternalLink className="w-3 h-3" /> Go to channel
                  </a>
                </div>
                <div className="bg-black/50 p-4 rounded-lg border border-white/10 font-mono text-xs text-gray-400 whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {selectedWarning.message_content || "No original content available."}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-white/5 bg-surface-darker/80 flex justify-end gap-3">
              <button 
                onClick={() => setSelectedWarning(null)}
                className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Close
              </button>
              <button 
                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium rounded-lg flex items-center gap-2 border border-red-500/20 transition-colors"
              >
                <Trash2 className="w-4 h-4" /> Revoke Warning
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
