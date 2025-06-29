from pathlib import Path
import datetime as dt
import yaml
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env if present

# ensure key exists
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not set. Create a .env file or export the variable.")

BASE = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE / "system_prompt.md"
TESTS_PATH = BASE / "tests.yaml"
RESULTS_DIR = BASE / "results"
RESULTS_DIR.mkdir(exist_ok=True)

client = OpenAI()

def load_system_prompt():
    return SYSTEM_PROMPT_PATH.read_text()

def load_tests():
    with open(TESTS_PATH, "r") as f:
        return yaml.safe_load(f)["tests"]

def run_test(system_prompt: str, context, turns, model="gpt-4.1-mini-2025-04-14"):
    messages = [{"role": "system", "content": system_prompt}] + context
    transcript = []
    print(f"\n🔄 Running test with {len(turns)} turns...")
    
    for idx, user_msg in enumerate(turns, 1):
        print(f"  ⏳ Processing turn {idx}/{len(turns)}...")
        messages.append({"role": "user", "content": user_msg})
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        assistant_msg = resp.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_msg})
        transcript.append((user_msg, assistant_msg))
        print(f"  ✅ Turn {idx} completed")
    
    print("✨ Test completed successfully!")
    return transcript

def md_escape(text: str) -> str:
    return text.replace("```", "``\`")

def dump_markdown(results):
    out_file = RESULTS_DIR / f"prompt_eval_{dt.datetime.now():%Y%m%d_%H%M}.md"
    with open(out_file, "w") as md:
        md.write(f"# Prompt Evaluation {dt.datetime.now():%Y-%m-%d %H:%M}\n\n")
        for test in results:
            md.write(f"## {test['name']}\n\n")
            for idx, (user, bot) in enumerate(test["transcript"], 1):
                md.write(f"**User {idx}:** {md_escape(user)}\n\n")
                md.write("\n".join(["> " + line for line in md_escape(bot).splitlines()]) + "\n\n")
            md.write("---\n\n")
    print(f"📝 Results written to {out_file}")

def main():
    print("🚀 Starting prompt evaluation...")
    print("📖 Loading system prompt and tests...")
    system_prompt = load_system_prompt()
    tests = load_tests()
    results = []
    
    print(f"\n📋 Found {len(tests)} tests to run")
    for idx, t in enumerate(tests, 1):
        print(f"\n🧪 Running test {idx}/{len(tests)}: {t['name']}")
        transcript = run_test(system_prompt, t.get("context", []), t["turns"])
        results.append({"name": t["name"], "transcript": transcript})
    
    print("\n💾 Saving results...")
    dump_markdown(results)
    print("\n🎉 All tests completed successfully!")

if __name__ == "__main__":
    main() 