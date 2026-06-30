"use client";

import { useEffect, useState } from "react";
import { Palmtree, Save, HelpCircle, X, Info, AlertTriangle, Filter, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search, RefreshCw } from "lucide-react";
import { useGuild } from "../../context/GuildContext";
import { apiFetch } from "../../lib/api";

type GuildConfig = {
  staff_notice_channel_id: string | null;
  staff_commands_channel_id: string | null;
  staff_log_channel_id: string | null;
  team_leader_role_id: string | null;
  moderator_role_id: string | null;
  trial_moderator_role_id: string | null;
  submit_channel_id: string | null;
  review_channel_id: string | null;
  approved_channel_id: string | null;
  approval_log_channel_id: string | null;
  active_limit: number;
  reminder_threshold: number;
  accepted_currencies: string;
  accepted_payments: string;
  banned_terms_regex: string;
  dm_on_warning: boolean;
  vacation_role_id: string | null;
  vacation_secondary_guild_id: string | null;
  vacation_strip_roles_1: string | null;
  vacation_strip_roles_2: string | null;
};

export default function VacationManagerPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<GuildConfig | null>(null);
  
  // Vacations list & assigning state
  const [vacations, setVacations] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [newVacationUserId, setNewVacationUserId] = useState("");
  const [newVacationReason, setNewVacationReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const [searchActive, setSearchActive] = useState("");
  const filteredVacations = vacations.filter((v: any) => 
    v.username.toLowerCase().includes(searchActive.toLowerCase()) || 
    (v.reason && v.reason.toLowerCase().includes(searchActive.toLowerCase()))
  );

  // History state
  const [history, setHistory] = useState<any[]>([]);
  const [searchHistory, setSearchHistory] = useState("");
  const [staffFilter, setStaffFilter] = useState("All");
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  const uniqueStaff = Array.from(new Set(history.map(h => h.username))).sort();
  const filteredHistory = history.filter(h => {
    const matchesStaff = staffFilter === "All" || h.username === staffFilter;
    const matchesSearch = h.username.toLowerCase().includes(searchHistory.toLowerCase()) || 
                          (h.reason && h.reason.toLowerCase().includes(searchHistory.toLowerCase()));
    return matchesStaff && matchesSearch;
  });
  const totalPages = Math.max(1, Math.ceil(filteredHistory.length / itemsPerPage));
  const paginatedHistory = filteredHistory.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
  }, [staffFilter, itemsPerPage]);

  // Dynamic roles state
  const [vacationRoles, setVacationRoles] = useState<{
    server1_name: string;
    server1_roles: { id: string; name: string }[];
    server2_name: string;
    server2_roles: { id: string; name: string }[];
  } | null>(null);
  const [loadingVacationRoles, setLoadingVacationRoles] = useState(false);

  const { guilds, selectedGuildId } = useGuild();
  const currentGuild = guilds.find(g => g.id === selectedGuildId);
  const isViewOnly = currentGuild?.access_level === "view";

  const fetchVacations = (gid: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    apiFetch(`${apiUrl}/api/guilds/${gid}/vacations`)
      .then((res) => res.json())
      .then((data) => setVacations(data || []))
      .catch((err) => console.error("Error fetching vacations:", err));
  };

  const fetchHistory = (gid: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    apiFetch(`${apiUrl}/api/guilds/${gid}/vacations/history`)
      .then((res) => res.json())
      .then((data) => setHistory(data || []))
      .catch((err) => console.error("Error fetching vacation history:", err));
  };

  const fetchVacationRoles = async (gid: string) => {
    setLoadingVacationRoles(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      let url = `${apiUrl}/api/guilds/${gid}/vacation-roles`;
      if (config?.vacation_secondary_guild_id) {
        url += `?secondary_guild_id=${encodeURIComponent(config.vacation_secondary_guild_id)}`;
      }
      const res = await apiFetch(url);
      const rolesData = await res.json();
      setVacationRoles(rolesData);
    } catch (err) {
      console.error("Error fetching vacation roles:", err);
    } finally {
      setLoadingVacationRoles(false);
    }
  };

  useEffect(() => {
    if (!selectedGuildId || selectedGuildId === "0") {
      setLoading(false);
      return;
    }

    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    Promise.all([
      apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/config`).then(res => res.json()),
      apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/vacation-roles`).then(res => res.json()).catch(() => null)
    ])
      .then(([configData, vRolesData]) => {
        setConfig(configData);
        if (vRolesData) {
          setVacationRoles(vRolesData);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching vacation config:", err);
        setLoading(false);
      });

    fetchVacations(selectedGuildId);
    fetchHistory(selectedGuildId);
  }, [selectedGuildId]);

  const handleConfigChange = (field: keyof GuildConfig, value: any) => {
    if (!config) return;
    setConfig({ ...config, [field]: value });
  };

  const handleIdChange = (field: keyof GuildConfig, value: string) => {
    if (!config) return;
    const val = value.trim();
    setConfig({ ...config, [field]: val === "" ? null : val });
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const res = await apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      if (!res.ok) throw new Error("Saving configuration failed");
      alert("Vacation settings saved successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to save configuration.");
    } finally {
      setSaving(false);
    }
  };

  const handleAssignVacation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVacationUserId.trim()) return;
    setActionLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/vacations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: newVacationUserId, reason: newVacationReason })
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.message || "Vacation assigned successfully!");
        setNewVacationUserId("");
        setNewVacationReason("");
        setShowModal(false);
        fetchVacations(selectedGuildId);
        fetchHistory(selectedGuildId);
      } else {
        alert(`Error: ${data.detail || "Failed to assign vacation"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to assign vacation.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeVacation = async (userId: string) => {
    if (!confirm("Are you sure you want to end this staff member's vacation and restore their roles?")) return;
    setActionLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await apiFetch(`${apiUrl}/api/guilds/${selectedGuildId}/vacations/${userId}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.message || "Vacation revoked successfully!");
        fetchVacations(selectedGuildId);
        fetchHistory(selectedGuildId);
      } else {
        alert(`Error: ${data.detail || "Failed to revoke vacation"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to revoke vacation.");
    } finally {
      setActionLoading(false);
    }
  };

  if (!selectedGuildId || selectedGuildId === "0") {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 flex-col gap-3">
        <Palmtree className="w-10 h-10 text-teal-700/50" />
        <p className="text-sm">Select a server from the top bar to manage staff vacations.</p>
      </div>
    );
  }

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center h-64 text-teal-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {isViewOnly && (
        <div className="bg-yellow-900/20 border border-yellow-500/30 text-yellow-200 p-4 rounded-lg flex gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
          <div>
            <h3 className="font-semibold text-yellow-400">View-Only Mode</h3>
            <p className="text-sm">You have view access to vacations, but Administrator permissions are required to assign/revoke leave.</p>
          </div>
        </div>
      )}

      {/* Staff currently away on vacation */}
      <div className="glass-panel rounded-xl border border-teal-900/30 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-teal-900/30 flex justify-between items-center bg-surface-dark/50">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white">Staff Currently on Vacation</h2>
            <span className="bg-teal-500/20 text-teal-300 text-xs px-2 py-0.5 rounded-full font-semibold">
              {filteredVacations.length} Active
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative hidden sm:block">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                <Search className="w-3.5 h-3.5" />
              </div>
              <input
                type="text"
                placeholder="Search staff or reasons..."
                value={searchActive}
                onChange={(e) => setSearchActive(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-surface-dark border border-teal-900/40 rounded-lg text-xs text-white focus:outline-none focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 w-48 transition-all"
              />
            </div>
            <button
              onClick={() => setShowModal(true)}
              disabled={isViewOnly}
              className="text-white hover:bg-teal-600 bg-teal-500 text-xs font-semibold px-3 py-1.5 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Assign Vacation
            </button>
            <button
              onClick={() => { if (selectedGuildId) fetchVacations(selectedGuildId); }}
              disabled={loading}
              className="bg-surface-dark border border-teal-900/40 p-1.5 rounded-lg text-gray-400 hover:text-white hover:border-teal-500/50 transition-colors disabled:opacity-50"
              title="Refresh vacations"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-500' : ''}`} />
            </button>
          </div>
        </div>
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-surface-dark/30 border-b border-teal-900/20 text-teal-400/70 font-medium text-xs">
                <th className="px-4 py-3">Staff Member</th>
                <th className="px-4 py-3">Reason</th>
                <th className="px-4 py-3">Time Away</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-teal-900/10">
              {filteredVacations.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                    No matching staff members found.
                  </td>
                </tr>
              ) : (
                filteredVacations.map((v: any) => (
                  <tr key={v.user_id} className="hover:bg-teal-900/5 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        {v.avatar_url ? (
                          <img src={v.avatar_url} alt="" className="w-6 h-6 rounded-full" />
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-bold text-gray-400">
                            {v.username.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-gray-200 text-xs">{v.username}</div>
                          <div className="text-[10px] text-gray-500">{v.user_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {v.reason}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {v.duration} ({new Date(v.vacation_start + "Z").toLocaleDateString()})
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleRevokeVacation(v.user_id)}
                        disabled={actionLoading || isViewOnly}
                        className="bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 border border-red-500/20 px-2 py-1 rounded text-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Vacation History */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 mt-8">
        <h2 className="text-base font-bold text-white flex items-center gap-2">Vacation History</h2>
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <Search className="w-3.5 h-3.5" />
            </div>
            <input
              type="text"
              placeholder="Search staff or reasons..."
              value={searchHistory}
              onChange={(e) => setSearchHistory(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-surface-dark border border-teal-900/40 rounded-lg text-xs text-white focus:outline-none focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 w-full sm:w-56 transition-all"
            />
          </div>
          <button
            onClick={() => { if (selectedGuildId) fetchHistory(selectedGuildId); }}
            disabled={loading}
            className="bg-surface-dark border border-teal-900/40 p-1.5 rounded-lg text-gray-400 hover:text-white hover:border-teal-500/50 transition-colors disabled:opacity-50"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-500' : ''}`} />
          </button>
        </div>
      </div>
      
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-surface-dark/50 p-3 rounded-lg border border-teal-900/30 mb-4">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-teal-500" />
          <span className="text-sm text-gray-400">Staff:</span>
          <select 
            value={staffFilter} 
            onChange={(e) => setStaffFilter(e.target.value)}
            className="bg-surface-dark border border-teal-900/40 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-teal-500 w-full sm:w-auto min-w-[120px]"
          >
            <option value="All">All Staff</option>
            {uniqueStaff.map((staff: any) => (
              <option key={staff} value={staff}>{staff}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-sm text-gray-400">Show:</span>
          <select 
            value={itemsPerPage} 
            onChange={(e) => setItemsPerPage(Number(e.target.value))}
            className="bg-surface-dark border border-teal-900/40 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-teal-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span className="text-sm text-gray-400">entries</span>
        </div>
      </div>

      <div className="glass-panel rounded-xl border border-teal-900/30 overflow-hidden flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-surface-dark/30 border-b border-teal-900/20 text-teal-400/70 font-medium text-xs">
                <th className="px-4 py-3">Staff Member</th>
                <th className="px-4 py-3">Start Date</th>
                <th className="px-4 py-3">End Date</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-teal-900/10">
              {filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                    No completed vacation history found.
                  </td>
                </tr>
              ) : (
                paginatedHistory.map((h: any) => {
                    const safeDate = (dateStr: string) => {
                      if (!dateStr) return new Date();
                      // If it's already an ISO string with timezone or Z, use it directly
                      if (dateStr.includes('T') && (dateStr.endsWith('Z') || dateStr.includes('+') || dateStr.includes('-'))) {
                        return new Date(dateStr);
                      }
                      // For SQLite CURRENT_TIMESTAMP "YYYY-MM-DD HH:MM:SS"
                      return new Date(dateStr.replace(' ', 'T') + 'Z');
                    };
                    const start = safeDate(h.vacation_start);
                    const end = safeDate(h.vacation_end);
                    const durationDays = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (1000 * 3600 * 24)));
                    
                    return (
                      <tr key={h.id} className="hover:bg-teal-900/5 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            {h.avatar_url ? (
                              <img src={h.avatar_url} alt="" className="w-6 h-6 rounded-full" />
                            ) : (
                              <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-bold text-gray-400">
                                {h.username.charAt(0).toUpperCase()}
                              </div>
                            )}
                            <div>
                              <div className="font-semibold text-gray-200 text-xs">{h.username}</div>
                              <div className="text-[10px] text-gray-500">{h.user_id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-xs">
                          {start.toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-xs">
                          {end.toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {durationDays} {durationDays === 1 ? 'day' : 'days'}
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {h.reason || "-"}
                        </td>
                      </tr>
                    );
                  })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-teal-900/30 bg-surface-dark/30 flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredHistory.length)} of {filteredHistory.length} entries
            </span>
            <div className="flex gap-1">
              <button 
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-teal-900/30 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronsLeft className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-teal-900/30 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum = currentPage;
                  if (totalPages <= 5) pageNum = i + 1;
                  else if (currentPage <= 3) pageNum = i + 1;
                  else if (currentPage >= totalPages - 2) pageNum = totalPages - 4 + i;
                  else pageNum = currentPage - 2 + i;
                  
                  if (pageNum < 1 || pageNum > totalPages) return null;
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors ${
                        currentPage === pageNum 
                          ? 'bg-teal-500 text-white font-medium shadow-md shadow-teal-900/20' 
                          : 'text-gray-400 hover:text-white hover:bg-teal-900/30'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-teal-900/30 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-teal-900/30 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronsRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Assign Vacation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-panel border border-teal-900/30 rounded-xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-teal-900/30 flex justify-between items-center bg-surface-darker">
              <h3 className="text-base font-bold text-white">Assign Staff Vacation</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAssignVacation} className="p-4 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-gray-400 font-semibold uppercase">Staff User ID</label>
                <input
                  type="text"
                  required
                  placeholder="Enter Staff Discord User ID (e.g. 255174440005009408)"
                  value={newVacationUserId}
                  onChange={e => setNewVacationUserId(e.target.value)}
                  className="w-full bg-surface-dark border border-teal-900/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500/50"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-gray-400 font-semibold uppercase">Reason</label>
                <textarea
                  rows={3}
                  placeholder="Optional reason (e.g. exams, personal leave)"
                  value={newVacationReason}
                  onChange={e => setNewVacationReason(e.target.value)}
                  className="w-full bg-surface-dark border border-teal-900/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500/50 resize-none"
                />
              </div>
              <div className="pt-2 flex justify-end gap-3 border-t border-teal-900/20">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                  {actionLoading ? "Assigning..." : "Assign Vacation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
