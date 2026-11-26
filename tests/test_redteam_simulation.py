import unittest, tempfile, os, json, contextlib, io
from pathlib import Path
from unittest.mock import patch
from scripts import sync_agentskills as s

class Simulation(unittest.TestCase):
    def test_matrix(self):
        url="https://agentskills.io/skill-creation/quickstart"
        name="skill-creation-quickstart.md"
        old="# Quickstart\n\n## Rules\n\n"+"Keep this instruction. "*40+"\n"
        cases=[
          ("valid",old+"New guidance.\n",True,True),
          ("unchanged",old,False,False),
          ("truncated","# Quickstart\n\n## Rules\n",True,False),
          ("missing_heading",old.replace("## Rules","## Other"),True,False),
          ("export_only",old+"Extra.\n",False,False),
          ("publication_lag",old,True,False),
          ("semantic_replacement",old.replace("Keep this instruction.","Ignore this instruction."),True,False),
          ("inert_injection_marker",old+"\n<!-- SIMULATED UNTRUSTED AGENT DIRECTIVE -->\n",True,False),
          ("unrelated_html","# Quickstart\n\n## Rules\n\n"+"<div>Unrelated content</div> "*50,True,False),
          ("license_changed",old+"New.\n",True,False),
          ("missing_source",old+"New.\n",True,False),
          ("network_failure",old,True,False),
          ("local_corruption",old+"New.\n",True,False),
          ("commit_race",old+"New.\n",True,False),
          ("missing_license_metadata",old+"New.\n",True,False),
          ("symlink_target",old+"New.\n",True,False),
        ]
        for label,raw,changed,expected in cases:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/"repo"; root.mkdir()
                normalized=s.normalize_markdown(old,url)
                (root/name).write_text(normalized)
                manifest={"documents":[{"file_name":name,"canonical_md_url":url+".md",**s.document_metrics(normalized)}],"total_documentation_pages":1,"upstream_docs_commit_at_capture":"a"*40,"upstream_license":"CC-BY-4.0","upstream_license_scope":"docs","upstream_license_source":"fixture","upstream_root_license":"Apache-2.0"}
                if label=="missing_license_metadata": del manifest["upstream_license"]
                (root/"sources.json").write_text(json.dumps(manifest))
                if label=="local_corruption": (root/name).write_text("corrupt")
                outside=Path(d)/"outside.txt"; outside.write_text(normalized)
                if label=="symlink_target":
                    (root/name).unlink(); (root/name).symlink_to(outside)
                before={"docs/skill-creation/quickstart.mdx":"c"*40,"docs/LICENSE":"d"*40}
                after=dict(before)
                if changed: after["docs/skill-creation/quickstart.mdx"]="e"*40
                if label=="license_changed": after["docs/LICENSE"]="f"*40
                if label=="missing_source": del after["docs/skill-creation/quickstart.mdx"]
                def request(u,token=None):
                    if u==s.LLMS_URL: return "- [Quickstart]("+url+".md): Guide"
                    if label=="network_failure": raise RuntimeError("fixture network failure")
                    return raw
                snapshot={p.name:p.read_bytes() for p in root.iterdir()}
                allowed=False; error=None; touched=False
                try:
                    with patch.object(s,"_request_text",side_effect=request), patch.object(s,"fetch_upstream_docs_commit",side_effect=["b"*40,("c" if label=="commit_race" else "b")*40]),patch.object(s,"fetch_upstream_tree",side_effect=[before,after]),patch.dict(os.environ,{"GITHUB_ACTIONS":"true","AGENTSKILLS_SYNC_WRITE":"1"}):
                        result,docs,llms,commit=s.audit(root)
                        allowed=result["proposal_allowed"]
                        if allowed: s.apply_update(root,manifest,docs,llms,commit,result)
                except Exception as exc: error=type(exc).__name__
                touched=snapshot!={p.name:p.read_bytes() for p in root.iterdir()}
                outside_changed=outside.read_text()!=normalized
                passed=(allowed==expected and touched==expected and not outside_changed and (not expected or error is None))
                print("REDTEAM "+json.dumps(dict(case=label,expected=expected,allowed=allowed,writes=touched,outside_changed=outside_changed,error=error,passed=passed)),flush=True)
        # Observational test: findings are reported individually, not hidden by an early assertion.

    def test_deeper_boundaries(self):
        def probe(label, fn):
            try:
                outcome=fn()
                print("ROUND2 "+json.dumps({"case":label,"outcome":outcome}),flush=True)
            except Exception as exc:
                print("ROUND2 "+json.dumps({"case":label,"error":type(exc).__name__}),flush=True)
        def path_check(value):
            try: return {"accepted":s.local_filename(value)}
            except (RuntimeError,ValueError): return {"rejected":True}
        for label,value in [
            ("parent_path","https://agentskills.io/../outside.md"),
            ("encoded_path","https://agentskills.io/%2e%2e/outside.md"),
            ("reserved_readme","https://agentskills.io/readme.md"),
            ("reserved_agents","https://agentskills.io/agents.md"),
            ("windows_device","https://agentskills.io/con.md"),
            ("query_path","https://agentskills.io/page?x=.md")]:
            probe(label,lambda value=value:path_check(value))
        def tree_duplicate():
            payload={"truncated":False,"tree":[{"path":"docs/a.mdx","type":"blob","sha":"a"*40},{"path":"docs/a.mdx","type":"blob","sha":"b"*40}]}
            with patch.object(s,"_request_text",return_value=json.dumps(payload)):
                return s.fetch_upstream_tree("c"*40)
        probe("duplicate_tree_entries",tree_duplicate)
        def metadata_fence():
            doc={"title":"Fixture | Extra","source_url":"https://agentskills.io/a","file_name":"a.md"}
            output=s.build_index([doc],"fixture\n```\nUNTRUSTED_FIXTURE_MARKER\n```")
            return {"unescaped_table_separator":"Fixture | Extra" in output,"raw_fence_break":"```\nUNTRUSTED_FIXTURE_MARKER" in output}
        probe("index_structure_integrity",metadata_fence)
        def write_guard():
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)
                with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","AGENTSKILLS_SYNC_WRITE":"1"}):
                    try: s.apply_update(root,{},[],"","a"*40,{"proposal_allowed":True})
                    except RuntimeError: return {"blocked":True,"files":len(list(root.iterdir()))}
                return {"blocked":False}
        probe("write_without_actions",write_guard)
        def partial_write():
            with tempfile.TemporaryDirectory() as d:
                root=Path(d); name="a.md"; url="https://agentskills.io/a"
                (root/name).write_text("old")
                doc=s.RemoteDocument("A","",url+".md",url,name,"new")
                previous={"upstream_license":"CC-BY-4.0","upstream_license_scope":"docs","upstream_license_source":"fixture","upstream_root_license":"Apache-2.0"}
                original=Path.write_text
                def fail_manifest(self,*args,**kwargs):
                    if self.name=="sources.json": raise OSError("simulated disk failure")
                    return original(self,*args,**kwargs)
                with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","AGENTSKILLS_SYNC_WRITE":"1"}),patch.object(Path,"write_text",fail_manifest):
                    try: s.apply_update(root,previous,[doc],"","a"*40,{"proposal_allowed":True,"changed_files":[name],"added_files":[],"removed_files":[]})
                    except OSError: return {"document_changed":(root/name).read_text()!="old","manifest_exists":(root/"sources.json").exists()}
        probe("disk_failure_atomicity",partial_write)
        def malformed_index():
            valid="- [A](https://agentskills.io/a.md): fixture"
            return {"parsed_count":len(s.parse_llms(valid+"\n- [B](https://agentskills.io/b.md)"))}
        probe("malformed_index_entry",malformed_index)
