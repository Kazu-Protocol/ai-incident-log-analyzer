from pathlib import Path
from streamlit.testing.v1 import AppTest
import analyzer

APP = Path(__file__).resolve().parents[1] / 'app.py'


def fake_ai(text, api_key, model, *, receipt):
    # A local test double; no network or production key is used.
    receipt.update(model=model, response_id='resp_test_only', input_tokens=123, output_tokens=456)
    return analyzer.demo_analyze(text)


def test_ai_flow_and_stale_result(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL', 'test-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
    monkeypatch.setattr(analyzer, 'llm_analyze', fake_ai)
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    assert at.title[0].value == 'AIによるログ分析と原因・対処方法の提案'
    assert not at.radio and not at.checkbox
    assert at.selectbox[0].label == '分析用ログを選ぶ'
    assert not at.button[0].disabled
    at.button[0].click().run()
    assert not at.exception
    assert at.success[0].value == 'AI解析が完了しました。'
    assert any('使用モデル：test-model' in m.value for m in at.markdown)
    assert not any('resp_test_only' in m.value for m in at.markdown)
    assert not any('AIへの接続記録' in e.label for e in at.expander)
    assert any('接続先への通信障害' in s.value for s in at.subheader)
    at.selectbox[0].select('通常ログ').run()
    assert not at.success
    at.button[0].click().run()
    assert not at.exception
    assert any('検出されませんでした' in w.value for w in at.warning)


def test_failed_request_clears_success_without_fallback(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL', 'test-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
    monkeypatch.setattr(analyzer, 'llm_analyze', fake_ai)
    at = AppTest.from_file(str(APP)).run()
    at.button[0].click().run()
    assert at.success
    def fail(*args, **kwargs):
        raise RuntimeError('private error details')
    monkeypatch.setattr(analyzer, 'llm_analyze', fail)
    at.button[0].click().run()
    assert not at.exception
    assert not at.success
    assert at.error
    assert 'private error details' not in at.error[0].value


def test_missing_key(monkeypatch):
    # No actual SDK call is made, regardless of any local secrets file.
    monkeypatch.setenv('OPENAI_API_KEY', ' ')
    monkeypatch.setenv('OPENAI_MODEL', 'test-model')
    at = AppTest.from_file(str(APP)).run()
    at.button[0].click().run()
    assert not at.exception
    assert at.error and not at.success
    assert 'APIキーとモデル名' in at.error[0].value
