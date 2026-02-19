import os

# Files that define the "Brain" of your project
# Since the script is at the root, these paths are direct and easy.
core_files = [
    'backend/app/main.py',
    'backend/app/services/stats_engine.py',
    'backend/app/repositories/data_repository.py',
    'architecture-law.md',
    'plan.md',
    'README.md'
]

output_file = 'AI_CONTEXT_DUMP.txt'

print("🛰️ Harvesting project context...")

with open(output_file, 'w', encoding='utf-8') as f:
    for file_path in core_files:
        if os.path.exists(file_path):
            f.write(f"\n--- START OF FILE: {file_path} ---\n")
            with open(file_path, 'r', encoding='utf-8') as content:
                f.write(content.read())
            f.write(f"\n--- END OF FILE: {file_path} ---\n")
            print(f"✅ Added: {file_path}")
        else:
            print(f"❌ Not Found: {file_path}")

print(f"\n🚀 Done! Copy the contents of {output_file} to your AI.")