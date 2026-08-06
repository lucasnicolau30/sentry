from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
@dataclass(frozen=True)
class SpecScenario:
    name:str; given:str; when:str; then:str; and_steps:tuple[str,...]=()
@dataclass(frozen=True)
class GitChange:
    revision:str|None; reference:str|None; files:tuple[str,...]; diff:str=''; statuses:dict[str,str]=None; changed_lines:dict[str,tuple[int,...]]=None; error:str|None=None
@dataclass(frozen=True)
class TestExecution:
    command:str; passed:int=0; failed:int=0; skipped:int=0; not_run:int=0; output:str=''; infrastructure_error:str|None=None; status:str|None=None; duration_seconds:float=0.0
@dataclass(frozen=True)
class CoverageData:
    global_percent:float|None; files:dict[str,float]; changed_percent:float|None=None; error:str|None=None; executed_lines:dict[str,tuple[int,...]]=None
class SpecReader(Protocol):
    def scenarios(self)->tuple[SpecScenario,...]: ...
class GitReader(Protocol):
    def change(self, reference:str|None=None)->GitChange: ...
class TestRunner(Protocol):
    def run(self, coverage_file:Path, timeout_seconds:int=300)->tuple[TestExecution,float|None]: ...
class CoverageReader(Protocol):
    def read(self, path:Path)->CoverageData: ...

