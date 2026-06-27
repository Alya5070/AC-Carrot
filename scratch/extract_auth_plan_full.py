import json

transcript_path = r"C:\Users\Gigabyte\.gemini\antigravity\brain\cd622651-746f-4377-83c3-83e2e6362836\.system_generated\logs\transcript.jsonl"

auth_plans = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        content = data.get("content", "")
        # Look for occurrences where implementation_plan.md contains "auth" or "oauth"
        if "implementation_plan" in content.lower() and "oauth" in content.lower():
            # Let's save the step index and the full content if it is under 30000 chars, or first 5000 chars
            auth_plans.append((data.get("step_index"), data.get("type"), content))

print(f"Found {len(auth_plans)} steps with OAuth/Auth plans.")
# Let's print the latest step content (or the one that seems most complete)
if auth_plans:
    latest = auth_plans[-1]
    print(f"=== Step {latest[0]} ({latest[1]}) ===")
    print(latest[2][:5000]) # First 5000 characters
