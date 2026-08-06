from pathlib import Path
from ..ports.inputs import SpecScenario
class MarkdownSpecAdapter:
    def __init__(self,path:Path): self.path=path
    def scenarios(self):
        text=self.path.read_text(encoding='utf-8'); result=[]; current=None; data={}
        for line in text.splitlines():
            if line.startswith('### Cenário:'):
                if current: result.append(SpecScenario(current,data.get('Dado',''),data.get('Quando',''),data.get('Então',''),tuple(data.get('E', '').split('|')) if data.get('E') else ()))
                current=line.split(':',1)[1].strip(); data={}
            elif line.startswith('- Dado:'): data['Dado']=line.split(':',1)[1].strip()
            elif line.startswith('- Quando:'): data['Quando']=line.split(':',1)[1].strip()
            elif line.startswith('- Então:'): data['Então']=line.split(':',1)[1].strip()
            elif line.startswith('- E:'): data['E']=line.split(':',1)[1].strip()
        if current: result.append(SpecScenario(current,data.get('Dado',''),data.get('Quando',''),data.get('Então','')))
        return tuple(result)
    def behaviors(self):
        text=self.path.read_text(encoding='utf-8'); result=[]; inside=False
        for line in text.splitlines():
            if line.startswith('### Behaviors'):
                inside=True; continue
            if inside and line.startswith('### '): break
            if inside and line.startswith('- **'):
                name=line.strip('- **').split('**')[0].strip()
                if name: result.append(name)
        return tuple(result)