"""
TARGETS.PY - target/capture bookkeeping for the Map, kept out of the environment class.
"""
from maspy import Any, Percept

class TargetTracker:
    # Returns the (x, y) coordinates of every registered target.
    def _target_positions(self):
        if not self.has(Percept("target", (Any, Any, Any))):
            return []
        targets = self.get(Percept("target", (Any, Any, Any)), all=True)
        return [(t.values[0], t.values[1]) for t in targets]

    # Returns a dictionary mapping (x, y) coordinates to target point values.
    def _target_values_map(self):
        if not self.has(Percept("target", (Any, Any, Any))):
            return {}
        targets = self.get(Percept("target", (Any, Any, Any)), all=True)
        return {(t.values[0], t.values[1]): t.values[2] for t in targets}

    # Positions of targets that have already been captured.
    def _captured_target_positions(self):
        if not self.has(Percept("captured_target", (Any, Any, Any))):
            return []
        captured = self.get(Percept("captured_target", (Any, Any, Any)), all=True)
        # c.values is (pos, val, agt), so pos is c.values[0].
        return [c.values[0] for c in captured]

    # Positions of targets that are still available for capture.
    def _remaining_target_positions(self):
        captured = self._captured_target_positions()
        return [pos for pos in self._target_positions() if pos not in captured]

    # _capture() - records the capture by storing (position, value, agent).
    def _capture(self, pos, val, agt):
        self.create(Percept("captured_target", (pos, val, agt)))
        self.print(f"{agt} captured the target at {pos} worth {val} points!")

        remaining = self._remaining_target_positions()
        self.targets_left.change(values=(len(remaining),))
        if not remaining:
            all_captures = self.get(Percept("captured_target", (Any, Any, Any)), all=True) or []
            # Rank agents by highest captured value.
            ranking = sorted(all_captures, key=lambda c: c.values[1], reverse=True)
            self.print(f"=== GAME OVER ===")
            for rank, cap in enumerate(ranking, 1):
                p, v, a = cap.values
                self.print(f"  {rank} Place: {a} with {v} points (at {p})")
