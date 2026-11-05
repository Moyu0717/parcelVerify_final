"""Short AI summary, Apply suggestion, the auto-run setting and the early-close dialog."""
from db import get_connection
from agent.runner import _check_proposal, investigate_case
from services.cases import get_case_context, list_cases
from tests.test_agent import ScriptedProvider, valid_report
from tests.test_case_completion import demo, ADMIN
from tests.test_ui_refactor import app, open_main, widget, healthy, approve_as_supervisor


def test_missing_weight_reweigh_is_reported_as_covered_by_the_open_task(demo):
    """PV-SHIP-021 live run: the AI named the missing-evidence finding for a reweigh. Not a failure."""
    path, _ = demo
    case = next(c for c in list_cases(path, ADMIN) if c['shipment_id'] == 'PV-SHIP-021')
    findings = {f['finding_id']: f for f in get_case_context(path, case['case_id'], ADMIN)['findings']}
    missing = [f for f, v in findings.items() if v['category'] == 'missing_evidence']
    assert missing
    with get_connection(path) as conn:
        handover = conn.execute("SELECT event_id FROM events WHERE shipment_id='PV-SHIP-021' AND event_type='handoff_submitted'").fetchone()[0]
        proposal = {'action_type': 'request_reweigh', 'source_event_id': handover, 'finding_ids': missing,
                    'reason': 'Handover weight is missing', 'evidence_ids': [handover], 'draft_message': ''}
        notes = {}
        checked, note = _check_proposal(conn, {'proposed_action': proposal}, 'PV-SHIP-021', {handover}, findings, notes)
    assert checked['proposed_action'] is None
    assert note.startswith('no new request needed')
    assert 'Provide' in notes['proposal_covered_by_task']


def _review(app, monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'private-test-value')
    provider = ScriptedProvider([{'done': True}, valid_report()])
    monkeypatch.setattr('ui.live.investigate_case', lambda path, case_id, actor, **kw: investigate_case(path, case_id, actor, provider=provider, **kw))
    return provider


def test_apply_suggestion_only_fills_the_request_form(app, monkeypatch):
    _review(app, monkeypatch)
    case_id = open_main(app)
    widget(app.button, 'Review evidence with AI').click().run()
    healthy(app)
    app.button(key='apply-suggestion-' + case_id).click().run()
    healthy(app)
    assert app.radio(key='request-type-' + case_id).value == 'request_reweigh'
    with get_connection(app.session_state.db_path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM action_requests WHERE case_id=?', (case_id,)).fetchone()[0] == 0, 'applying must not file anything'
    app.button(key='send-request-' + case_id).click().run()
    with get_connection(app.session_state.db_path) as conn:
        assert conn.execute("SELECT status FROM action_requests WHERE case_id=?", (case_id,)).fetchone()[0] == 'proposed'


def test_full_ai_review_opens_in_a_dialog(app, monkeypatch):
    _review(app, monkeypatch)
    case_id = open_main(app)
    widget(app.button, 'Review evidence with AI').click().run()
    assert not [m for m in app.markdown if 'Agent trace' in m.value]
    app.button(key='ai-details-' + case_id).click().run()
    healthy(app)
    assert [m for m in app.markdown if 'Agent trace' in m.value]


def test_auto_run_setting_runs_one_review_once(app, monkeypatch):
    provider = _review(app, monkeypatch)
    app.session_state.secondary_view = 'Settings'
    app.run()
    app.toggle(key='auto_ai_widget').set_value(True).run()
    assert app.session_state.auto_ai_review is True
    app.session_state.secondary_view = None
    open_main(app)
    healthy(app)
    assert len(provider.calls) == 2  # one selection call, one report call
    app.run()
    assert len(provider.calls) == 2


def test_stop_waiting_is_a_button_that_opens_a_dialog(app):
    case_id = open_main(app)
    app.button(key='send-request-' + case_id).click().run()
    approve_as_supervisor(app)
    assert not [e for e in app.expander if e.label == 'Stop waiting and close the case']
    assert not [r for r in app.radio if r.key == 'outcome-' + case_id]
    app.button(key='stop-waiting-' + case_id).click().run()
    healthy(app)
    assert [r for r in app.radio if r.key == 'outcome-' + case_id]


def test_more_details_opens_in_a_dialog_without_nested_dialog_errors(app):
    case_id = open_main(app)
    assert not [e for e in app.expander if e.label == 'Evidence and photos']
    app.button(key='show-details-' + case_id).click().run()
    healthy(app)
    assert not [b for b in app.button if (b.key or '').startswith(('weight-enlarge-', 'linked-enlarge-'))]
    assert any('Compare the recorded photos' in s.value for s in app.subheader)


def test_activity_page_shows_the_last_opened_case_and_role_dropdown_switches(app):
    case_id = open_main(app)
    assert not [h for h in app.get('html') if 'Activity log' in str(getattr(h, 'proto', ''))]
    app.button(key='send-request-' + case_id).click().run()
    app.button(key='nav-Activity').click().run()
    healthy(app)
    assert app.selectbox(key='activity_case_widget').value == case_id
    assert any('Activity' == t.value for t in app.title)
    app.selectbox(key='desktop-role').set_value('approver').run()
    healthy(app)
    assert app.session_state.actor_role == 'approver'
