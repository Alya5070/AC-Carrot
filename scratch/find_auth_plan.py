import json

transcript_path = r"C:\Users\Gigabyte\.gemini\antigravity\brain\cd622651-746f-4377-83c3-83e2e6362836\.system_generated\logs\transcript.jsonl"

found_steps = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        content = data.get("content", "")
        # Look for steps writing to implementation_plan.md containing "auth" or "login"
        if "implementation_plan" in content.lower() and "auth" in content.lower():
            found_steps.append((data.get("step_index"), data.get("type"), content[:500]))

print(f"Found {len(found_steps)} steps")
for step_idx, step_type, text in found_steps:
    print(f"Step {step_idx} ({step_type}): {text}\n")
