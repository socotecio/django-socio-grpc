def rreplace(s: str, old: str, new: str, occurrence: str):
    if not old:
        return s
    li = s.rsplit(old, occurrence)
    return new.join(li)
