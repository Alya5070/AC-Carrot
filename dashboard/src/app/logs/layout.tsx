"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function LogsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="max-w-7xl mx-auto flex flex-col gap-6">
      {/* Logs Navigation Top Bar */}
      <nav className="glass-panel border border-teal-900/30 rounded-xl p-2 flex flex-row items-center gap-2 overflow-x-auto">
        <div className="text-sm font-semibold text-teal-600/70 uppercase tracking-wider px-4 border-r border-teal-900/30 mr-2 shrink-0">
          Logs
        </div>
        <Link 
          href="/logs/warnings" 
          className={`px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${pathname === '/logs/warnings' ? 'bg-teal-500/10 text-teal-400 font-medium' : 'text-gray-400 hover:text-white hover:bg-teal-500/10'}`}
        >
          Verbal Warnings
        </Link>
        <Link 
          href="/logs/requests" 
          className={`px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${pathname === '/logs/requests' ? 'bg-teal-500/10 text-teal-400 font-medium' : 'text-gray-400 hover:text-white hover:bg-teal-500/10'}`}
        >
          Paid Requests
        </Link>
        <Link 
          href="/logs/reminders" 
          className={`px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${pathname === '/logs/reminders' ? 'bg-teal-500/10 text-teal-400 font-medium' : 'text-gray-400 hover:text-white hover:bg-teal-500/10'}`}
        >
          Active Reminders
        </Link>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0">
        {children}
      </div>
    </div>
  );
}
