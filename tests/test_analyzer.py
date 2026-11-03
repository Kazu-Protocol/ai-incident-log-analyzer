from pathlib import Path
from types import SimpleNamespace
import pytest
from analyzer import demo_analyze, llm_analyze, redact, validate_log, levels

SAMPLES = Path(__file__).resolve().parents[1] / 'samples'

@pytest.mark.parametrize('name,title,lines', [
    ('timeout', '接続先への通信障害', [2, 3, 4]),
    ('disk', 'ディスク容量の逼迫', [2, 3, 4]),
    ('auth', '認証・権限の問題', [2, 3]),
])
def test_samples(name, title, lines):
    text = (SAMPLES / f'{name}.log').read_text()
    report = demo_analyze(text)
    assert report == demo_analyze(text)
    assert report.findings[0].title == title
    assert report.findings[0].evidence_lines == lines

@pytest.mark.parametrize('text', ['', ' \n', 'あ' * 8001, 'x\n' * 201, 'hello\x00world'])
def test_invalid_input(text):
    with pytest.raises(ValueError):
        validate_log(text)


def test_normal_and_unknown_are_not_asserted_healthy():
    assert not demo_analyze((SAMPLES / 'normal.log').read_text()).findings
    assert not demo_analyze('ERROR strange new error').findings


def test_redaction():
    text = 'token=abc password="two words" api_key=xyz Bearer abcdef user@example.com 192.0.2.1 sk-demo123'
    result = redact(text)
    for secret in ['abc', 'two words', 'xyz', 'abcdef', 'user@example.com', '192.0.2.1', 'sk-demo123']:
        assert secret not in result
    assert len(result.splitlines()) == len(text.splitlines())


def test_levels():
    assert levels('ERROR x\nWARNING y\nplain') == {'ERROR': 1, 'WARN': 1, 'OTHER': 1}


class FakeClient:
    def __init__(self, report):
        self.responses = self
        self.report = report
        self.kwargs = None
    def parse(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_parsed=self.report)


def test_llm_adapter_without_network():
    client = FakeClient(demo_analyze('ERROR timeout'))
    report = llm_analyze('ERROR timeout', 'test-only', 'test-model', client)
    assert report.findings[0].evidence_lines == [1]
    assert client.kwargs['store'] is False
    assert client.kwargs['input'] == '1: ERROR timeout'
    assert client.kwargs['max_output_tokens'] == 2200


def test_missing_key_no_request():
    with pytest.raises(ValueError):
        llm_analyze('ERROR timeout', '', 'test-model')

@pytest.mark.parametrize('invalid', [None, {'summary':'x','findings':[{'title':'x','severity':'高','hypothesis':'x','evidence_lines':[99],'checks':['x']}],'limitations':'x'}])
def test_rejects_incomplete_or_invalid_evidence(invalid):
    with pytest.raises(ValueError):
        llm_analyze('ERROR timeout', 'test-only', 'test-model', FakeClient(invalid))
