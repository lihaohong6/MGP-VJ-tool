def auto_lj(s: str) -> str:
    if s.isalnum():
        return s
    return "{{lj|" + s + "}}"
