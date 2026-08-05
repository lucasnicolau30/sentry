from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
@dataclass(frozen=True)
class SpecScenario:
    name:str; given:str; when:str; then:str; and_steps:tuple[str,...]=()
@dataclass(frozen=True)
class GitChange:
    revision:str|None; reference:str|None; files:tuple[str,...]; diff:str=''
@dataclass(frozen=True)
class TestExecution:
    command:str; passed:int=0; failed:int=0; skipped:int=0; output:str=''; infrastructure_error:str|None=None
@dataclass(frozen=True)
class CoverageData:
    global_percent:float|None; files:dict[str,float]; changed_percent:float|None=None; error:str|None=None
class SpecReader(Protocol):
    def scenarios(self)->tuple[SpecScenario,...]: ...
class GitReader(Protocol):
    def change(self, reference:str|None=None)->GitChange: ...
class TestRunner(Protocol):
    def run(self, timeout_seconds:int=300)->TestExecution: ...
class CoverageReader(Protocol):
    def read(self, path:Path)->CoverageData: ...