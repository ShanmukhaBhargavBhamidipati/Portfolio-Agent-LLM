import json

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_final_prompt(prompt_path, schema_path):
    system_prompt = load_prompt(prompt_path)

    if "{SCHEMA}" not in system_prompt:
        raise ValueError("The prompt file must contain the placeholder {SCHEMA}")

    schema = load_schema(schema_path)
    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

    return system_prompt.replace("{SCHEMA}", schema_str)