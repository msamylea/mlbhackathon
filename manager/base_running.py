from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random

@dataclass 
class BaseState:
    def __init__(self):
        self._bases = [None, None, None] 
    
    @property
    def first(self):
        return self._bases[0]
        
    @first.setter
    def first(self, value):
        self._bases[0] = value
        
    @property
    def second(self):
        return self._bases[1]
        
    @second.setter 
    def second(self, value):
        self._bases[1] = value
        
    @property
    def third(self):
        return self._bases[2]
        
    @third.setter
    def third(self, value):
        self._bases[2] = value
    
    def __getitem__(self, index):
        return self._bases[index]
        
    def __setitem__(self, index, value):
        self._bases[index] = value
        
    def to_list(self) -> List[Optional[str]]:
        return self._bases.copy()
    
    @classmethod
    def from_list(cls, bases: List[Optional[str]]) -> 'BaseState':
        state = cls()
        for i, runner in enumerate(bases[:3]):
            state._bases[i] = runner
        return state
        
    def format(self) -> str:
        state_parts = []
        base_names = ['first', 'second', 'third']
        for i, runner in enumerate(self._bases):
            if runner:
                state_parts.append(f"{runner} on {base_names[i]}")
        return ', '.join(state_parts) if state_parts else "Bases empty"

class BaseRunningManager:
    """Manages all base running logic and state updates"""
    
    @staticmethod
    def determine_advancement(play_type: str, base_state: BaseState, outs: int) -> Tuple[Dict[str, bool], List[str]]:
        """
        Determine how runners should advance based on the play type.
        Returns (advancement_dict, scored_runners).
        """
        
        advancement = {
            "advance_first": False,
            "advance_second": False,
            "advance_third": False,
            "score_run": False
        }
        scored_runners = []
        
        play_type = play_type.lower()
        runners = base_state.to_list()

        if 'hits a home run' in play_type:
            scored_runners.extend([runner for runner in runners if runner])

            advancement["score_run"] = True

        elif 'triples' in play_type:
            if base_state.third:
                scored_runners.append(base_state.third)
            if base_state.second:
                scored_runners.append(base_state.second)
            if base_state.first:
                scored_runners.append(base_state.first)
            advancement["advance_third"] = True

        elif 'doubles' in play_type:

            if base_state.third:
                scored_runners.append(base_state.third)
            if base_state.second:
                scored_runners.append(base_state.second)
            if base_state.first:
                advancement["advance_third"] = True
            advancement["advance_second"] = True

        elif 'singles' in play_type:

            if base_state.third:
                scored_runners.append(base_state.third)
            elif base_state.second:
                random.choice([lambda: scored_runners.append(base_state.second), lambda: advancement.update({"advance_third": True})])()
            if base_state.first:
                advancement["advance_second"] = True
            advancement["advance_first"] = True

        elif 'walk' in play_type:
            # Force advancement only
            if base_state.third and base_state.second and base_state.first:
                scored_runners.append(base_state.third)
            if base_state.second and base_state.first:
                advancement["advance_third"] = True
            if base_state.first:
                advancement["advance_second"] = True
            advancement["advance_first"] = True

        elif 'grounds out' in play_type:
            pass

        elif any(out_type in play_type for out_type in ['flies out', 'flyout', 'fly out']):
            if base_state.third and outs < 2:
                scored_runners.append(base_state.third)
        
        return advancement, scored_runners

    @staticmethod
    def update_base_state(
        current_state: BaseState,
        batter_name: str,
        advancement: Dict[str, bool],
        scored_runners: List[str]
    ) -> BaseState:
        """Update base state based on runner advancement."""
        new_state = BaseState()
        
        base_list = current_state.to_list()
        
        runners = current_state.to_list()
        runners = [runner if runner not in scored_runners else None for runner in runners]
        
        current_state = BaseState.from_list(runners)
        
        if not any(advancement.values()):
            new_state._bases = base_list
            return new_state

        if advancement["advance_first"]:
            if current_state.third:
                scored_runners.append(current_state.third)
            new_state.third = current_state.second
            new_state.second = current_state.first
            new_state.first = batter_name


        elif advancement["advance_second"]:
            if current_state.third:
                scored_runners.append(current_state.third)
            if current_state.second:
                scored_runners.append(current_state.second)
            new_state.third = current_state.first
            new_state.second = batter_name
            if current_state.third:
                scored_runners.append(current_state.third)


        elif advancement["advance_third"]:
            scored_runners.extend([r for r in runners if r])
            new_state.third = batter_name
            scored_runners.extend([r for r in base_list if r])


        elif advancement["score_run"]:
            scored_runners.extend([r for r in runners if r])
            scored_runners.append(batter_name)

            
        return new_state

    @staticmethod
    def process_out(
        current_state: BaseState,
        play_type: str,
        fielder_position: str,
        outs: int
    ) -> Tuple[BaseState, List[str]]:
        """Process base running on outs (groundout, flyout, etc)"""
        scored_runners = []
        new_state = BaseState.from_list(current_state.to_list())

        if 'flyout' in play_type or 'flies out' in play_type:
            if outs < 2:
                if current_state.third and fielder_position in ['LF', 'CF', 'RF']:
                    scored_runners.append(current_state.third)
                    new_state.third = None

        elif 'groundout' in play_type or 'grounds out' in play_type:
            if current_state.third:
                scored_runners.append(current_state.third)
                new_state.third = None
            if current_state.second and outs < 2:
                new_state.third = current_state.second
                new_state.second = None
            if current_state.first and outs < 2:
                new_state.second = current_state.first
                new_state.first = None

        return new_state, scored_runners