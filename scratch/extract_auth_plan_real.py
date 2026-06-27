import json

transcript_path = r"C:\Users\Gigabyte\.gemini\antigravity\brain\cd622651-746f-4377-83c3-83e2e6362836\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        step_idx = data.get("step_index")
        content = data.get("content", "")
        # Look for step index 240 or 242 or any write_to_file call containing "OAuth"
        if step_idx in [240, 242]:
            print(f"=== STEP {step_idx} ===")
            print(content)
        
        # Or look for write_to_file tool_calls containing implementation_plan.md
        tool_calls = data.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                if tc.get("name") == "write_to_file":
                    args = tc.get("args", {})
                    target = args.get("TargetFile", "")
                    code = args.get("CodeContent", "")
                    if "implementation_plan" in target and "oauth" in code.lower():
                        print(f"=== Found write_to_file in Step {step_idx} ===")
                        print(code)
