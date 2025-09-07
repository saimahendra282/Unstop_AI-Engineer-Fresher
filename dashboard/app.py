import requests
import streamlit as st
import os
import pandas as pd

API_BASE = os.environ.get('API_BASE', 'http://localhost:8000')

st.set_page_config(page_title="Support AI Inbox", layout="wide")

st.title(" AI-Powered Support Inbox ")

# Get available filter categories
try:
    filter_response = requests.get(f"{API_BASE}/emails/filters")
    if filter_response.status_code == 200:
        filter_data = filter_response.json()
        available_categories = ["all"] + filter_data["categories"]
        category_details = filter_data.get("category_details", {})
    else:
        available_categories = ["all", "support", "query", "request", "urgent", "help", "billing", "technical", "account"]
        category_details = {}
except:
    available_categories = ["all", "support", "query", "request", "urgent", "help", "billing", "technical", "account"]
    category_details = {}

# Filter Selection Row
st.subheader("📧 Email Filtering & Loading")
filter_col, load_col, inbox_col, refresh_col = st.columns([2,1,1,1])

with filter_col:
    selected_filter = st.selectbox(
        "🔍 Filter Category", 
        available_categories,
        format_func=lambda x: {
            "all": "🌟 All Categories",
            "support": "🆘 Support",
            "query": "❓ Query", 
            "request": "📝 Request",
            "urgent": "🚨 Urgent",
            "help": "🤝 Help",
            "billing": "💰 Billing",
            "technical": "🔧 Technical", 
            "account": "👤 Account"
        }.get(x, x.replace("_", " ").title())
    )

with load_col:
    if st.button("📁 Load CSV"):
        try:
            r = requests.post(f"{API_BASE}/emails/load_csv")
            if r.status_code == 200:
                st.success(f"✅ {r.json()}")
            else:
                st.error(f"❌ Load failed: {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ API server not running")

with inbox_col:
    if st.button("📧 Load Inbox", help=f"Load emails from Gmail filtered by: {selected_filter}"):
        try:
            with st.spinner(f"🔍 Fetching {selected_filter} emails from Gmail..."):
                r = requests.post(f"{API_BASE}/emails/load_inbox", params={
                    "filter_category": selected_filter,
                    "limit": 100
                })
                if r.status_code == 200:
                    result = r.json()
                    if result.get('reason') == 'success':
                        st.success(f"✅ Found {result.get('fetched', 0)} emails, stored {result.get('stored', 0)} new ones!")
                        if result.get('filter_category'):
                            st.info(f"🏷️ Filter applied: **{result['filter_category'].replace('_', ' ').title()}**")
                    else:
                        st.warning(f"⚠️ {result.get('reason', 'Unknown issue')}")
                else:
                    st.error(f"❌ Load failed: {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ API server not running")

with refresh_col:
    if st.button("🔄 Refresh"):
        st.experimental_rerun()

# Stats button
col_stats = st.columns([1])[0]
with col_stats:
    if st.button("📊 Show Analytics"):
        st.session_state['show_stats'] = True

st.subheader("📬 Email Queue")
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

if emails:
    st.write(f"**Found {len(emails)} emails** (sorted by priority)")
    
    # Enhanced email selection with preview
    email_options = []
    for email in emails:
        priority_icon = "🚨" if email.get('priority') == 'urgent' else "📧"
        sentiment_icon = {"positive": "😊", "negative": "😠", "neutral": "😐"}.get(email.get('sentiment', 'neutral'), "😐")
        category = email.get('matched_category', 'general').replace('_', ' ').title()
        category_icon = {
            "Support": "🆘", "Query": "❓", "Request": "📝", "Urgent": "🚨", 
            "Help": "🤝", "Billing": "💰", "Technical": "🔧", "Account": "👤"
        }.get(category, "📂")
        
        preview = f"{priority_icon} {sentiment_icon} {category_icon} {category} | {email.get('subject', 'No Subject')[:50]}..."
        email_options.append((email['id'], preview))
    
    selected = st.selectbox(
        "Select Email", 
        [opt[0] for opt in email_options] if email_options else [],
        format_func=lambda x: next(opt[1] for opt in email_options if opt[0] == x) if email_options else ""
    )
else:
    st.info("🔍 No emails found. Try loading emails with the buttons above!")
    selected = None

if selected:
    try:
        detail = requests.get(f"{API_BASE}/emails/{selected}").json()
        
        # Enhanced email details display
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            st.metric("Priority", detail.get('priority', 'Unknown').title(), 
                     help=f"Score: {detail.get('priority_score', 0)}")
        with col2:
            st.metric("Sentiment", detail.get('sentiment', 'Unknown').title())
        with col3:
            category = detail.get('matched_category', 'general').replace('_', ' ').title()
            st.metric("Category", category)
            
        st.write("**📧 Email Details:**")
        display_data = {
            "Subject": detail.get('subject', 'No Subject'),
            "From": detail.get('sender', 'Unknown'),
            "Received": detail.get('received_at', 'Unknown'),
            "Status": detail.get('status', 'Unknown')
        }
        for key, value in display_data.items():
            st.write(f"**{key}:** {value}")
            
        with st.expander("📄 Email Body"):
            st.write(detail.get('body','No content'))
            
        # Show extraction results
        extraction = detail.get('extraction', {})
        if extraction:
            with st.expander("🔍 Extracted Information"):
                if extraction.get('phones'):
                    st.write("📞 **Phone Numbers:**", ", ".join(extraction['phones']))
                if extraction.get('emails'):
                    st.write("📧 **Email Addresses:**", ", ".join(extraction['emails']))
                if extraction.get('key_phrases'):
                    st.write("🔑 **Key Phrases:**", ", ".join(extraction['key_phrases']))
                if extraction.get('urgency_reason'):
                    st.write("⚡ **Urgency Trigger:**", extraction['urgency_reason'])
        
        if st.button("🤖 Generate Draft"):
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
