# Looker model for the executive / sales GTM surface.
# Illustrative LookML over the same BigQuery marts that the Streamlit app and the
# Apps Script ops web app read. Demonstrates the semantic layer that gives every
# self-service user one consistent definition of ARR, NRR, Rule of 40, etc.

connection: "gtm_warehouse"   # a BigQuery connection in production

include: "/views/*.view.lkml"

explore: gtm_company_monthly {
  label: "GTM Economics"
  description: "Time-aware SaaS efficiency: ARR, retention, Rule of 40, efficiency ratios."
}

explore: account_positioning {
  label: "Account Portfolio"
  description: "Account-level priority, recommended play, expected value, governance status."
}
