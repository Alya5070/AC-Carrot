"use client";

import { PenTool } from "lucide-react";

export default function BuilderPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <PenTool className="text-teal-400 w-8 h-8" />
          Message Builder
        </h1>
        <p className="text-gray-400 mt-1">Design and send custom embeds and reaction roles.</p>
      </div>

      <div className="glass-panel p-8 rounded-xl border border-teal-900/30 min-h-[500px] flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-xl font-medium text-white">Coming Soon</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            The visual message builder is currently under development. Once completed, you will be able to design Discord embeds directly from your browser.
          </p>
        </div>
      </div>
    </div>
  );
}
