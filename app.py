from pathlib import Path
import hashlib
import os
import streamlit as st
from analyzer import MAX_BYTES, levels, llm_analyze, markdown_report, redact, validate_log

TITLE = 'AIによるログ分析と原因・対処方法の提案'
st.set_page_config(page_title=TITLE, layout='wide')
# This app has no sidebar or header controls. Hide Streamlit's hosting toolbar.
st.markdown('<style>header[data-testid="stHeader"] {display: none;}</style>', unsafe_allow_html=True)
st.title(TITLE)


def setting(name):
    value = os.getenv(name, '')
    if value:
        return value
    try:
        return str(st.secrets.get(name, ''))
    except FileNotFoundError:
        return ''


sample_dir = Path(__file__).parent / 'samples'
selection = st.selectbox('分析用ログを選ぶ', ['接続タイムアウト', 'ディスク逼迫', '認証失敗', '通常ログ', '自由入力'])
names = {'接続タイムアウト': 'timeout.log', 'ディスク逼迫': 'disk.log', '認証失敗': 'auth.log', '通常ログ': 'normal.log'}
if st.session_state.get('selection') != selection:
    st.session_state['log_input'] = (sample_dir / names[selection]).read_text() if selection in names else ''
    st.session_state['selection'] = selection
uploaded = st.file_uploader('またはUTF-8の.log / .txtを読み込む', type=['log', 'txt'])
st.caption('個人情報や機密情報を含むログは入力しないでください')
text = st.text_area('解析するログ', key='log_input', height=210)
if uploaded is not None:
    if uploaded.size > MAX_BYTES:
        st.error('ファイルは24,000バイト以内にしてください。')
        st.stop()
    try:
        text = uploaded.getvalue().decode('utf-8')
    except UnicodeDecodeError:
        st.error('UTF-8形式で保存したファイルを選択してください。')
        st.stop()
    st.caption('アップロードしたファイルを優先しています。貼り付け入力に戻すにはファイルを解除してください。')

try:
    validate_log(text)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()
safe_text = redact(text)
a, b, c = st.columns(3)
a.metric('ログ行数', len(text.splitlines()))
b.metric('ERROR / FATAL / CRITICAL', sum(v for k, v in levels(text).items() if k in ('ERROR', 'FATAL', 'CRITICAL')))
c.metric('WARN', levels(text).get('WARN', 0))
with st.expander('AIに送るログを確認', expanded=True):
    st.code('\n'.join(f'{i:03d} | {line}' for i, line in enumerate(safe_text.splitlines(), 1)), language='text')

# Bind results to the current input and model. Never fall back to a rule demo.
model = setting('OPENAI_MODEL')
fingerprint = hashlib.sha256(('ai-only\0' + model + '\0' + text).encode()).hexdigest()
if st.button('ログを解析', type='primary'):
    st.session_state.pop('result', None)
    try:
        receipt = {}
        with st.spinner('AIがログを解析しています…'):
            report = llm_analyze(safe_text, setting('OPENAI_API_KEY'), model, receipt=receipt)
        st.session_state['result'] = (fingerprint, report, receipt.get('model', model))
    except ValueError as exc:
        st.error(str(exc))
    except Exception:
        # Do not expose SDK errors that could contain request details.
        st.error('AIによる解析に失敗しました。APIキー・モデルの利用権限・残高・通信状況を確認してください。')
result = st.session_state.get('result')
if result and result[0] == fingerprint:
    report = result[1]
    st.subheader('初動調査レポート')
    st.success('AI解析が完了しました。')
    st.write('使用モデル：' + str(result[2]))
    st.write(report.summary)
    if not report.findings:
        st.warning('対応する兆候は検出されませんでした。正常性を保証する結果ではありません。')
    for f in report.findings:
        with st.container(border=True):
            st.subheader(f'[{f.severity}] {f.title}')
            st.write('**考えられる原因**')
            st.write(f.hypothesis)
            st.caption('判断の根拠となるログ行：' + ', '.join(map(str, f.evidence_lines)))
            lines = safe_text.splitlines()
            st.code('\n'.join(f'{i:03d} | {lines[i-1]}' for i in f.evidence_lines), language='text')
            st.write('**次に確認すること**')
            for check in f.checks:
                st.write('• ' + check)
    with st.expander('追加調査が必要な点・解析の範囲'):
        st.write(report.limitations)
        st.caption('原因の確定には、監視情報や設定変更の履歴などとの照合が必要です。')
    st.download_button('レポートをMarkdownで保存', markdown_report(report, 'AI解析'), 'incident-report.md', 'text/markdown')
