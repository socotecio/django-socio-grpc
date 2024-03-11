def rreplace(s: str, old: str, new: str, max_split: int):
    if not old:
        return s
    li = s.rsplit(old, max_split)
    return new.join(li)
