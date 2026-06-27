"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";

export default function GuildWarningRedirect() {
  const router = useRouter();
  const params = useParams();
  
  useEffect(() => {
    const guildId = params?.guildId;
    const warningId = params?.warningId;
    if (guildId && warningId) {
      router.replace(`/logs/warnings?guildId=${guildId}&warningId=${warningId}`);
    } else {
      router.replace("/logs/warnings");
    }
  }, [params, router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh] text-teal-400">
      <div className="animate-pulse">Loading warning details...</div>
    </div>
  );
}
