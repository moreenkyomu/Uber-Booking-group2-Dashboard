# Uber Group 2 — Streamlit Dashboard

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python -m streamlit run app.py`.
5. Upload `Dataset_FinalProject_Group2(3).xlsx` in the sidebar.

The dashboard calculates KPIs from filtered records, includes eight interactive charts, data quality checks, cancellation reasons and CSV export.

**Interpretation safeguards:** Booking value is not profit. Repeated booking IDs are flagged, not silently deleted. Missing ratings and values are preserved as missing, since they often depend on booking status.
