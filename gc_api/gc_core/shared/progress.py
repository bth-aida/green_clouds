"""Module handling progress status"""

### external imports
import os
import secrets
import string

from pydantic import BaseModel

# progress dir
progress_dir = "progress_tmp"
os.makedirs(progress_dir, exist_ok=True)


def get_key(ksize: int) -> str:
    """Retuns a random key of length ksize"""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(ksize))


def get_tqdm_progress(filepath: str) -> int | None:
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return None

    with open(filepath, "rb") as f:
        # go to end of file
        f.seek(0, os.SEEK_END)
        pointer = f.tell()

        # read until %
        while pointer > 0:
            pointer -= 1
            f.seek(pointer)
            if f.read(1) == b"%":
                break

        # read numbers
        num_str = ""
        while pointer > 0:
            pointer -= 1
            f.seek(pointer)
            fchar = f.read(1).decode()
            if fchar.isdigit():
                num_str += str(fchar)
            else:
                break

        return int(num_str[::-1])


class ProgressItem(BaseModel):
    steps: int
    increment: float
    current: int


class Progress:
    def __init__(self) -> None:
        self.increment_stack: list[ProgressItem] = []
        self.progress: float = 0
        self.id = get_key(10)
        self.fpath = f"{progress_dir}/{self.id}.txt"

    def push(self, steps: int):
        """Add new layer of progress with a number of steps"""
        new_increment = 100 / steps
        if len(self.increment_stack) > 0:
            pr_item = self.increment_stack[-1]
            new_increment = pr_item.increment / steps
        self.increment_stack.append(
            ProgressItem(steps=steps, increment=new_increment, current=0)
        )

    def update(self, update_progress: bool = True):
        """Increment progress by 1"""
        if len(self.increment_stack) == 0:
            return
        # get current progress layer, increment it
        pr_item = self.increment_stack[-1]
        pr_item.current += 1

        # update global progress
        if update_progress:
            self.progress += pr_item.increment

        if pr_item.current == pr_item.steps:
            self.increment_stack.pop()
            self.update(update_progress=False)

    def file_fill(self):
        """Fill out file progress to 100%"""
        pr_item = self.increment_stack[-1]
        self.progress += pr_item.increment * (100 - pr_item.current)

    def file_update(self):
        """Update by reading progress from output file"""
        prog = get_tqdm_progress(self.fpath)
        if prog is not None:
            pr_item = self.increment_stack[-1]

            delta = prog - pr_item.current
            self.progress += pr_item.increment * delta
            pr_item.current = prog

    def pop(self):
        if len(self.increment_stack) == 0:
            raise IndexError("Pop called with an empty progress stack")
        self.increment_stack.pop()

    def get_progress(self) -> int:
        """Get current global progress"""
        self.file_update()

        return int(self.progress + 0.5)
