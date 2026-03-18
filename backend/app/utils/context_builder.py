def build_context(messages):
    return [
        {"role": m.get("role") if isinstance(m, dict) else m[0], 
         "content": m.get("content") if isinstance(m, dict) else m[1]}
        for m in messages[-5:]
    ]