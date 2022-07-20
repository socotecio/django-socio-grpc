from collections.abc import Iterable


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


class ProtoComment:
    def __init__(self, comments):
        if isinstance(comments, str):
            # INFO - AM - 20/07/2022 - if only pass a string we do not want to display a empty comment
            if not comments:
                self.comments = []
            else:
                self.comments = [comments]
        elif isinstance(comments, Iterable):
            self.comments = comments

    def __iter__(self):
        return iter(self.comments)

    def __bool__(self):
        return len(self.comments) != 0
