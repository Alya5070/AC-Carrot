"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import { LogIn, LogOut } from "lucide-react";

export function LoginButton() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="flex items-center gap-3 px-3 py-2">
        <div className="w-8 h-8 rounded-full bg-surface-darker animate-pulse"></div>
        <div className="flex-1 min-w-0">
          <div className="h-4 w-20 bg-surface-darker rounded animate-pulse mb-1"></div>
          <div className="h-3 w-16 bg-surface-darker rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (session && session.user) {
    return (
      <div className="flex items-center gap-3 px-3 py-2 group">
        <img 
          src={session.user.image || `https://cdn.discordapp.com/embed/avatars/0.png`} 
          alt="Avatar" 
          className="w-8 h-8 rounded-full border border-teal-900/30"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{session.user.name}</p>
          <button 
            onClick={() => signOut()}
            className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors mt-0.5"
          >
            <LogOut className="w-3 h-3" />
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-3 py-2">
      <button 
        onClick={() => signIn("discord")}
        className="w-full flex items-center justify-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors shadow-lg shadow-[#5865F2]/20"
      >
        <LogIn className="w-4 h-4" />
        Login with Discord
      </button>
    </div>
  );
}
