"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiFetch } from "../lib/api";

export type GuildInfo = {
  id: string;
  name: string;
  icon: string | null;
  access_level?: "admin" | "view";
};

interface GuildContextType {
  guilds: GuildInfo[];
  selectedGuildId: string;
  setSelectedGuildId: (id: string) => void;
  loading: boolean;
}

const GuildContext = createContext<GuildContextType | undefined>(undefined);

export function GuildProvider({ children }: { children: ReactNode }) {
  const [guilds, setGuilds] = useState<GuildInfo[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    apiFetch(`${apiUrl}/api/guilds`)
      .then(res => res.json())
      .then(data => {
        if (data.guilds && data.guilds.length > 0) {
          setGuilds(data.guilds);
          setSelectedGuildId(data.guilds[0].id);
        } else {
          setGuilds([{ id: "0", name: "Global / Default Server", icon: null }]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching guilds:", err);
        setGuilds([{ id: "0", name: "Global / Default Server", icon: null }]);
        setLoading(false);
      });
  }, []);

  return (
    <GuildContext.Provider value={{ guilds, selectedGuildId, setSelectedGuildId, loading }}>
      {children}
    </GuildContext.Provider>
  );
}

export function useGuild() {
  const context = useContext(GuildContext);
  if (context === undefined) {
    throw new Error("useGuild must be used within a GuildProvider");
  }
  return context;
}
