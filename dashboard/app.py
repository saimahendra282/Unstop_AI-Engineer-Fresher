import requests
import streamlit as st
import os
import pandas as pd

API_BASE = os.environ.get('API_BASE', 'http://localhost:8000')

st.set_page_config(page_title="Support AI Inbox", layout="wide")

st.title("AI-Powered Support Inbox")

col_load, col_inbox, col_refresh, col_stats = st.columns([1,1,1,1])
with col_load:
    if st.button("📁 Load CSV"):
        try:
            r = requests.post(f"{API_BASE}/emails/load_csv")
            if r.status_code == 200:
                st.success(f"✅ {r.json()}")
            else:
                st.error(f"❌ Load failed: {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ API server not running")

with col_inbox:
    if st.button("📧 Load Inbox"):
        try:
            with st.spinner("Fetching emails from Gmail..."):
                r = requests.post(f"{API_BASE}/emails/load_inbox")
                if r.status_code == 200:
                    result = r.json()
                    if result.get('reason') == 'success':
                        st.success(f"✅ Inbox: {result.get('stored', 0)} emails loaded")
                    else:
                        st.error(f"❌ Inbox load failed: {result.get('reason', 'Unknown error')}")
                else:
                    st.error(f"❌ Load failed: {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ API server not running")

with col_refresh:
    if st.button("🔄 Refresh"):
        st.experimental_rerun()
        
with col_stats:
    if st.button("📊 Show Stats"):
        st.session_state['show_stats'] = True

st.subheader("Queue")
try:
    resp = requests.get(f"{API_BASE}/emails/")
    if resp.status_code == 200:
        emails = resp.json()
    else:
        emails = []
        st.error(f"API error: {resp.status_code}")
except requests.exceptions.ConnectionError:
    st.error("⚠️ API server not running. Start it with: `uvicorn backend.app.main:app --reload`")
    emails = []

selected = st.selectbox("Select Email", [e['id'] for e in emails] if emails else [])

if selected:
    try:
        detail = requests.get(f"{API_BASE}/emails/{selected}").json()
        st.write({k: v for k, v in detail.items() if k != 'body'})
        with st.expander("Body"):
            st.write(detail.get('body',''))
        if st.button("Generate Draft"):
            try:
                d = requests.post(f"{API_BASE}/emails/{selected}/draft").json()
                st.session_state['draft'] = d.get('draft','')
            except Exception as e:
                st.error(f"Draft generation failed: {e}")
        draft = st.text_area("Draft", value=st.session_state.get('draft',''), height=200)
        
        col_send, col_mark = st.columns([1,1])
        with col_send:
            if st.button("📧 Send Reply"):
                if draft:
                    try:
                        result = requests.post(f"{API_BASE}/emails/{selected}/send", 
                                             json={"draft": draft}).json()
                        if result.get('success'):
                            st.success(f"✅ Reply sent successfully! {result.get('message', '')}")
                            st.session_state['draft'] = ''  # Clear draft after sending
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ Failed to send: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Send failed: {e}")
                else:
                    st.warning("Please generate or enter a draft first")
        
        with col_mark:
            if st.button("✅ Mark Responded"):
                st.success("Email marked as responded (manual override)")
    except Exception as e:
        st.error(f"Failed to load email details: {e}")
else:
    st.info("No email selected")

# Bulk actions
st.subheader("Bulk Actions")
col_bulk1, col_bulk2 = st.columns([1,1])
with col_bulk1:
    if st.button("📧 Send All Urgent Replies"):
        try:
            result = requests.post(f"{API_BASE}/emails/send_bulk?priority_filter=urgent").json()
            st.success(f"Sent {result.get('sent', 0)} urgent replies. Failed: {result.get('failed', 0)}")
        except Exception as e:
            st.error(f"Bulk send failed: {e}")
with col_bulk2:
    if st.button("📧 Send All Pending Replies"):
        try:
            result = requests.post(f"{API_BASE}/emails/send_bulk").json()
            st.success(f"Sent {result.get('sent', 0)} total replies. Failed: {result.get('failed', 0)}")
        except Exception as e:
            st.error(f"Bulk send failed: {e}")

if st.session_state.get('show_stats'):
    try:
        stats = requests.get(f"{API_BASE}/emails/stats").json()
        st.subheader("Analytics Dashboard")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Emails", stats.get('total_emails', 0))
        c2.metric("Last 24h", stats.get('total_last_24h', 0))
        c3.metric("Urgent", stats.get('urgent', 0))
        c4.metric("Responded", stats.get('responded', 0))
        c5.metric("Pending", stats.get('pending', 0))
        
        if stats.get('avg_response_time_minutes'):
            st.metric("Avg Response Time", f"{stats['avg_response_time_minutes']} min")
        
        st.subheader("Sentiment Distribution")
        st.bar_chart(pd.DataFrame.from_dict(stats.get('sentiment_counts', {}), orient='index', columns=['count']))
    except Exception as e:
        st.error(f"Failed to load stats: {e}")
