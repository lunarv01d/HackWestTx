import time

from collections import deque
from threading import Lock
from pynput import mouse


class DoomTracker:

    def __init__(
        self,
        fire_seconds=1200,
        recovery_multiplier=2.0,
        activity_window=10,
        min_scrolls=3,
    ):
        # How many seconds of sustained scrolling
        # before the tree completely dies.
        self.fire_seconds = fire_seconds

        # How quickly the tree recovers while taking a break.
        # 2.0 = recovers twice as fast as it deteriorates.
        self.recovery_multiplier = recovery_multiplier

        # Number of recent seconds considered when deciding
        # whether the user is actively scrolling.
        self.activity_window = activity_window

        # Minimum scroll events inside activity_window
        # before we consider it doom scrolling.
        self.min_scrolls = min_scrolls

        self.doom_seconds = 0.0

        self.scroll_events = deque()

        self.last_update = time.monotonic()

        self.lock = Lock()

        # Start global mouse listener
        self.listener = mouse.Listener(
            on_scroll=self._on_scroll
        )

        self.listener.start()

    def _on_scroll(self, x, y, dx, dy):
        now = time.monotonic()

        with self.lock:
            self.scroll_events.append(now)

    def update(self):
        now = time.monotonic()

        with self.lock:
            elapsed = now - self.last_update
            self.last_update = now

            # Remove old scroll events
            cutoff = now - self.activity_window

            while (
                self.scroll_events
                and self.scroll_events[0] < cutoff
            ):
                self.scroll_events.popleft()

            # Are we actively scrolling?
            scrolling = (
                len(self.scroll_events)
                >= self.min_scrolls
            )

            if scrolling:
                # Tree deteriorates
                self.doom_seconds += elapsed

                self.doom_seconds = min(
                    self.doom_seconds,
                    self.fire_seconds,
                )

            else:
                # Taking a break makes the tree recover
                self.doom_seconds -= (
                    elapsed
                    * self.recovery_multiplier
                )

                self.doom_seconds = max(
                    0,
                    self.doom_seconds,
                )

            # Convert accumulated doom time into
            # tree health from 100 -> 0
            tree_health = (
                1
                - (
                    self.doom_seconds
                    / self.fire_seconds
                )
            ) * 100

            tree_health = max(
                0,
                min(100, tree_health),
            )

            return (
                tree_health,
                self.doom_seconds,
                scrolling,
            )

    def stop(self):
        self.listener.stop()