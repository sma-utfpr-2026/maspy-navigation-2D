"""
TARGETS.PY - target/capture bookkeeping for the Map, kept out of the environment class.
"""

from maspy import Any, Percept


# TargetTracker - reads and updates the "target"/"captured_target" percepts of a Map.
class TargetTracker:
    # Positions of every target.
    def _target_positions(self):
        if not self.has(Percept("target", (Any, Any))):
            return []
        targets = self.get(Percept("target", (Any, Any)), all=True)
        return [t.values for t in targets]

    # Positions already captured.
    def _captured_target_positions(self):
        if not self.has(Percept("captured_target", (Any, Any))):
            return []
        captured = self.get(Percept("captured_target", (Any, Any)), all=True)
        return [c.values[0] for c in captured]

    # Targets still up for capture.
    def _remaining_target_positions(self):
        captured = self._captured_target_positions()
        return [t for t in self._target_positions() if t not in captured]

    # _capture() - record the capture and publish how many targets are left.
    def _capture(self, pos, agt):
        self.create(Percept("captured_target", (pos, agt)))
        self.print(f"{agt} captured the target at {pos}")

        remaining = self._remaining_target_positions()
        self.targets_left.change(values=(len(remaining),))
        if not remaining:
            winners = sorted({c.values[1] for c in
                              self.get(Percept("captured_target", (Any, Any)), all=True) or []})
            self.print(f"GAME OVER - all targets captured by {winners}. "
                       f"Close the pygame window when done.")
