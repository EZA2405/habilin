"""Package an explicit file allowlist; runtime credentials never enter the archives."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission'
source=[ROOT/name for name in ['README.md','AGENT_SPEC.md','AGENTS.md','STATE.md','.gitignore','SUBMISSION_REQUIREMENTS.md','ESTATE_PH_RESEARCH.md','ACTIONABILITY_RESEARCH.md']]
source += [p for folder in ['habilin','tests','scripts'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.html','.css','.js','.json'}]
source=sorted(set(source))
assert all('.runtime' not in p.parts and '.build' not in p.parts and p.suffix!='.env' for p in source)
with ZipFile(OUT/'Habilin-Source.zip','w',ZIP_DEFLATED) as archive:
    for p in source:archive.write(p,'Habilin/'+str(p.relative_to(ROOT)))
    # Keep the README's local submission-guide link usable inside the source archive.
    for name in ['START_HERE.md','Habilin-Idea-Brief.md','REVIEW_NOTES.md','template_requirements.json']:
        archive.write(OUT/name,'Habilin/submission/'+name)

required=['Registration-TO-FILL.xlsx','Habilin-Technical-Document.docx','Habilin-Presentation.pptx','Habilin-Presentation.pdf',
          'InternationalAI-Habilin-DemoVideo.mp4','Habilin-Security-Self-Assessment.docx',
          'Habilin-Execution-Evidence.docx','Habilin-Demo-Video-Guide.docx','Habilin-Source.zip',
          'Habilin-DemoVideo.srt','Habilin-Demo-Script.md','Habilin-Presentation-Speaker-Notes.md',
          'Habilin-Idea-Brief.md','execution-evidence.json','offline-replay-evidence.json','test-results.json','video-verification.json','template_requirements.json',
          'START_HERE.md','REGISTRATION-EMAIL-DRAFT.txt','SUBMISSION-EMAIL-DRAFT.txt','REVIEW_NOTES.md']
files=[OUT/name for name in required]+sorted((OUT/'screenshots').glob('*.png'))
assert all(p.exists() and p.stat().st_size>0 for p in files)
manifest={'prepared_not_submitted':True,'missing':['Real team details','Student eligibility and private proof','Registration and acknowledgment','Final topic acceptance'],
          'files':[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
files.append(OUT/'MANIFEST.json')
with ZipFile(OUT/'Habilin-Submission-Kit.zip','w',ZIP_DEFLATED) as archive:
    for p in source:archive.write(p,'Habilin-Submission/'+str(p.relative_to(ROOT)))
    for p in files:archive.write(p,'Habilin-Submission/submission/'+str(p.relative_to(OUT)))
with ZipFile(OUT/'Habilin-Submission-Kit.zip') as archive:
    assert archive.testzip() is None
    assert not any('.runtime' in n or '.env' in n or 'access.json' in n or '.db' in n for n in archive.namelist())
print(f"Source: {len(source)} files. Complete kit: {(OUT/'Habilin-Submission-Kit.zip').stat().st_size:,} bytes. Team fields remain unfinished.")
