from __future__ import annotations
import subprocess
from pathlib import Path
from ..ports.inputs import GitChange, TestExecution, CoverageData
class LocalGitAdapter:
    def __init__(self,root:Path): self.root=root
    def change(self,reference=None):
        def run(*args): return subprocess.run(['git',*args],cwd=self.root,text=True,capture_output=True,check=False)
        rev=run('rev-parse','HEAD'); base=reference or (run('rev-parse','HEAD~1').stdout.strip() if rev.returncode==0 else None)
        if rev.returncode!=0: return GitChange(None,base,(), '')
        names=run('diff','--name-only',base,'HEAD').stdout.splitlines() if base else []
        diff=run('diff',base,'HEAD').stdout if base else ''
        return GitChange(rev.stdout.strip(),base,tuple(names),diff)
class PytestAdapter:
    def __init__(self,root:Path,command='pytest'): self.root=root; self.command=command
    def run(self,timeout_seconds=300):
        try: p=subprocess.run(self.command,cwd=self.root,shell=True,text=True,capture_output=True,timeout=timeout_seconds)
        except FileNotFoundError: return TestExecution(self.command,infrastructure_error='pytest ausente')
        except subprocess.TimeoutExpired: return TestExecution(self.command,infrastructure_error='timeout')
        return TestExecution(self.command,failed=0 if p.returncode==0 else 1,output=p.stdout+p.stderr)
class CoverageAdapter:
    def read(self,path):
        if not path.exists(): return CoverageData(None,{},error='arquivo de cobertura ausente')
        return CoverageData(None,{},error='formato de cobertura não suportado')