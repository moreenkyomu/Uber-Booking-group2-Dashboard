import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Uber Booking Analytics | Group 2', layout='wide')
st.title('Uber Ride Booking Performance Dashboard')
st.caption('2024 NCR booking data | Operational performance and booking-value analytics')

@st.cache_data(show_spinner=False)
def load_data(file_bytes):
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name='ncr_ride_bookings')
    df = raw.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(r'[^a-z0-9]+','_',regex=True).str.strip('_')
    for c in df.select_dtypes(include='object').columns:
        df[c] = df[c].apply(lambda v: v.strip().strip('"') if isinstance(v,str) else v)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['booking_datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['time'].astype(str), errors='coerce')
    for c in ['booking_value','ride_distance','driver_ratings','customer_rating','avg_vtat','avg_ctat']:
        df[c] = pd.to_numeric(df[c],errors='coerce')
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['hour'] = df['booking_datetime'].dt.hour
    df['completed'] = df['booking_status'].eq('Completed')
    df['cancelled'] = df['booking_status'].isin(['Cancelled by Driver','Cancelled by Customer'])
    return raw, df

file = st.sidebar.file_uploader('Upload Group 2 Excel dataset', type=['xlsx'])
if file is None:
    st.info('Upload Dataset_FinalProject_Group2(3).xlsx to begin. The app reads the ncr_ride_bookings sheet.')
    st.stop()
try:
    raw, data = load_data(file.getvalue())
except Exception as exc:
    st.error(f'Unable to read workbook: {exc}')
    st.stop()

st.sidebar.header('Filters')
dates = data['date'].dropna()
if dates.empty:
    st.error('No valid dates were found.')
    st.stop()
selected_dates = st.sidebar.date_input('Booking date range', value=(dates.min().date(),dates.max().date()),min_value=dates.min().date(),max_value=dates.max().date())
vehicles = st.sidebar.multiselect('Vehicle type',sorted(data['vehicle_type'].dropna().unique()),default=sorted(data['vehicle_type'].dropna().unique()))
statuses = st.sidebar.multiselect('Booking status',sorted(data['booking_status'].dropna().unique()),default=sorted(data['booking_status'].dropna().unique()))
pickups = st.sidebar.multiselect('Pickup locations (optional)',sorted(data['pickup_location'].dropna().unique()))
filtered = data[data['vehicle_type'].isin(vehicles) & data['booking_status'].isin(statuses)].copy()
if len(selected_dates)==2:
    filtered = filtered[filtered['date'].between(pd.Timestamp(selected_dates[0]),pd.Timestamp(selected_dates[1]))]
if pickups:
    filtered=filtered[filtered['pickup_location'].isin(pickups)]

st.subheader('Data validation')
q1,q2,q3,q4=st.columns(4)
q1.metric('Source rows',f'{len(raw):,}')
q2.metric('Exact duplicate rows',f'{raw.duplicated().sum():,}')
q3.metric('Repeated booking IDs',f'{data.booking_id.duplicated().sum():,}')
q4.metric('Invalid dates',f'{data.date.isna().sum():,}')
with st.expander('Missing values and data quality details'):
    missing = pd.DataFrame({'missing_count':data.isna().sum(),'missing_pct':(data.isna().mean()*100).round(2)})
    st.dataframe(missing, use_container_width=True)
    st.warning('Missing ratings, payment methods and booking values often reflect booking status. Do not replace them with zero. Repeated booking IDs require investigation rather than automatic deletion.')
    duplicates = data[data.duplicated('booking_id',keep=False)].sort_values('booking_id')
    st.dataframe(duplicates.head(100),use_container_width=True)

n=len(filtered)
completed=filtered[filtered['completed']]
cancelled=filtered['cancelled'].sum()
value=completed['booking_value'].sum(min_count=1)
avg_value=completed['booking_value'].mean()
cols=st.columns(6)
metrics=[('Total bookings',n),('Completed',len(completed)),('Completion rate',100*len(completed)/n if n else 0),('Cancellation rate',100*cancelled/n if n else 0),('Completed booking value',value),('Avg completed value',avg_value)]
for i,(label,val) in enumerate(metrics):
    if i in [2,3]: display=f'{val:.1f}%'
    elif i in [4,5]: display=f'{val:,.2f}' if pd.notna(val) else 'N/A'
    else: display=f'{val:,.0f}'
    cols[i].metric(label,display)
st.caption('Booking value is not profit or platform net revenue. All metrics reflect the currently selected filters.')
if filtered.empty:
    st.warning('No records match the selected filters.')
    st.stop()

left,right=st.columns(2)
with left:
    status=filtered['booking_status'].value_counts().rename_axis('Status').reset_index(name='Bookings')
    st.plotly_chart(px.bar(status,x='Status',y='Bookings',title='Bookings by status'),use_container_width=True)
with right:
    monthly=filtered.groupby('month').size().reset_index(name='Bookings').sort_values('month')
    st.plotly_chart(px.line(monthly,x='month',y='Bookings',markers=True,title='Monthly booking trend'),use_container_width=True)
left,right=st.columns(2)
with left:
    v=filtered.groupby('vehicle_type').agg(Bookings=('completed','size'),Completed=('completed','sum')).reset_index()
    v['Completion rate (%)']=100*v['Completed']/v['Bookings']
    st.plotly_chart(px.bar(v,x='vehicle_type',y='Completion rate (%)',hover_data=['Bookings'],title='Completion rate by vehicle'),use_container_width=True)
with right:
    top=filtered['pickup_location'].value_counts().head(10).rename_axis('Pickup location').reset_index(name='Bookings')
    st.plotly_chart(px.bar(top,x='Bookings',y='Pickup location',orientation='h',title='Top 10 pickup locations'),use_container_width=True)
left,right=st.columns(2)
with left:
    scatter=completed[['ride_distance','booking_value','vehicle_type']].dropna()
    if len(scatter)>5000: scatter=scatter.sample(5000,random_state=42)
    st.plotly_chart(px.scatter(scatter,x='ride_distance',y='booking_value',color='vehicle_type',opacity=.4,title='Distance vs completed booking value (sample up to 5,000)'),use_container_width=True)
with right:
    st.plotly_chart(px.histogram(completed.dropna(subset=['customer_rating']),x='customer_rating',nbins=20,title='Customer rating distribution (completed rides)'),use_container_width=True)
left,right=st.columns(2)
with left:
    pm=completed['payment_method'].value_counts().rename_axis('Payment method').reset_index(name='Bookings')
    st.plotly_chart(px.bar(pm,x='Payment method',y='Bookings',title='Payment methods for completed rides'),use_container_width=True)
with right:
    hours=filtered.groupby('hour').size().reset_index(name='Bookings')
    st.plotly_chart(px.line(hours,x='hour',y='Bookings',markers=True,title='Bookings by hour'),use_container_width=True)

st.subheader('Operational investigation')
reason_cols=['reason_for_cancelling_by_customer','driver_cancellation_reason','incomplete_rides_reason']
for reason in reason_cols:
    if reason in filtered:
        counts=filtered[reason].dropna().value_counts()
        if not counts.empty:
            st.write(reason.replace('_',' ').title())
            st.dataframe(counts.rename_axis('Reason').reset_index(name='Bookings'),use_container_width=True)
st.subheader('Monthly growth')
monthly['Growth (%)']=monthly['Bookings'].pct_change()*100
st.dataframe(monthly,use_container_width=True)
st.subheader('Filtered data')
st.dataframe(filtered.head(1000),use_container_width=True)
st.download_button('Download filtered data as CSV',filtered.to_csv(index=False).encode('utf-8'),'uber_filtered_data.csv','text/csv')
st.markdown('**Recommended decisions:** Investigate high driver-cancellation segments and stated reasons; review low completion-rate vehicle categories alongside their sample sizes; align staffing with peak booking hours and high-demand pickup locations; monitor completion and cancellation rates after changes. These are proposals, not proven causal findings.')
