# ParcelVerify

ParcelVerify helps a logistics company check what happened to a parcel when it passes through outside delivery partners. It compares the recorded handovers (weight, package count, seal, photos, data access), flags differences, and walks a reviewer through asking the partner for proof, getting a second person's approval, reviewing the reply and recording an outcome.

All shipments, partners, people and photos in the app are synthetic. No message ever leaves the demo.

- Live demo: https://parcelverifyfinal.streamlit.app/
- Built with Python 3.11, Streamlit and SQLite. Optional AI review uses Groq.

## Try the demo

Each browser gets its own fresh demo workspace. Use the yellow **Act as** menu in the header to switch between the four demo roles: Administrator, Investigator, Supervisor and Partner. **Reset demo** starts a new workspace.

Three cases show the main situations:

| Case | What it shows |
|---|---|
| PV-DEMO-001 | The parcel weighed 2.00 kg before dispatch and 1.85 kg at handover. Its photo also matches another shipment's photo, and there is unusual data access. |
| PV-SHIP-011 | A difference that has a documented, approved explanation (repackaging) and an authorized data export. |
| PV-SHIP-021 | The handover weight was never recorded, so a partner task is already waiting for it. |

A typical walkthrough on PV-DEMO-001:

1. **Check.** Open the case from Home. The 3D map shows each recorded stop; the red building is the record that differs.
2. **Ask for proof.** Choose what you need (weigh again, new photo, count packages) and send the request.
3. **Approve.** The person who asked cannot approve their own request. Switch to Supervisor, give a reason and press **Approve & send to partner**.
4. **Review the reply.** Switch back to answer as the partner, then accept the new evidence or ask again.
5. **Finish.** Record *Verified* or *Close with open questions* with a reason. Every step appears on the Activity page.

On a case that is waiting for a partner, **Stop waiting and close the case** lets you close it early. It refuses *Verified* while required evidence is still missing.

## How the AI review works

AI review is optional and only runs when a person clicks **Review evidence with AI** (or turns on auto-run in Settings).

- One read-only investigator model (Groq, `openai/gpt-oss-120b` on the live app) chooses from a fixed list of read-only tools, such as reading the case, comparing handovers and checking access scope.
- The server checks every citation in the report against the records that were actually retrieved, and removes claims about what a photo shows, because the model reads text only.
- If the report supports a follow-up, it can suggest a request. **Apply suggestion** only fills in the request form. A person still sends it, and a different person must approve it. The AI can never approve, send or close anything.
- Weight, file hash and image hash comparisons are plain code, not AI.
- If AI is not configured or the free quota is used up, everything else keeps working.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe start.py
```

Then open http://localhost:8501. On macOS or Linux use `.venv/bin/python`.

To turn on AI review, copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and add your own Groq API key. That file is ignored by Git. On Streamlit Community Cloud, paste the same settings into **Manage app > Settings > Secrets** and reboot the app. The built-in guards keep usage under Groq's free-tier limits: 3 reviews per workspace per hour, 60 model requests per day, and token-per-minute and per-day caps.

## Tests

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe qa/evaluate_demo.py
```

The test suite uses temporary databases and scripted AI responses, so it makes no network calls. `qa/evaluate_demo.py` checks that the rules find the expected issues in the three demo cases and raise no false alerts on the 56 clean shipments. `qa/real_ai_acceptance.py --confirm-free-plan` runs one real AI review if `GROQ_API_KEY` is set in the environment.

## Project layout

| Path | Contents |
|---|---|
| `app.py`, `start.py` | Streamlit entry point and local launcher |
| `ui/` | Pages, header, case workflow, 3D map and styling |
| `services/` | Rules, cases, requests and approvals, evidence and audit log |
| `agent/` | The Groq AI review: tool list, run loop and report checks |
| `seed.py`, `demo_fixtures.py`, `fixtures/`, `assets/` | Synthetic demo data and images |
| `schema.sql`, `db.py`, `workspace.py` | Per-visitor SQLite workspaces |
| `tests/` | Automated tests |

## Limitations

- This is a demo. The role menu shows who may do which step; it is not real sign-in.
- A flag means "needs review". It does not show that a partner did anything wrong.
- The AI reads text records only and never inspects photos. Its wording can still be imprecise, so reviewers should read the cited records, not only the summary.
- Package-count shortfalls are marked for review, because the data has no per-item scan records.
- Demo data expires after 24 hours of inactivity and may be lost when the hosted app restarts. Use the recovery token in Settings to return to a workspace.
- There is no measurement yet of whether ParcelVerify saves review time.
