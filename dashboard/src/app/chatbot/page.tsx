"use client";

import { Bot } from "lucide-react";

export default function ChatbotPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Bot className="text-teal-400 w-8 h-8" />
          Chatbot Configuration
        </h1>
        <p className="text-gray-400 mt-1">Manage interactive menus, automated responses, and button workflows.</p>
      </div>

      <div className="glass-panel p-8 rounded-xl border border-teal-900/30 min-h-[500px] flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-xl font-medium text-white">Coming Soon</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            The Chatbot editor is currently under development. Once completed, you will be able to fully customize the bot's conversational flows and interactive buttons from here.
          </p>
        </div>
      </div>
    </div>
  );
}
