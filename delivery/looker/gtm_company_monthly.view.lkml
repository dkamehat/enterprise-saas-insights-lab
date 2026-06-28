# Semantic definitions for the company GTM time series.
# One governed definition per metric, reused by every Looker user — the antidote
# to "every deck computes NRR differently". Mirrors saas_insights.gtm so the
# warehouse and the BI layer never disagree.

view: gtm_company_monthly {
  sql_table_name: `gtm_marts.gtm_company_monthly` ;;

  dimension: month {
    type: date_month
    sql: CAST(${TABLE}.month AS DATE) ;;
    primary_key: yes
  }

  # --- Point-in-time ratios already materialised in the warehouse --------------
  dimension: nrr_ttm_pct { type: number sql: ${TABLE}.nrr_ttm_pct ;; }
  dimension: grr_ttm_pct { type: number sql: ${TABLE}.grr_ttm_pct ;; }
  dimension: arr_growth_yoy_pct { type: number sql: ${TABLE}.arr_growth_yoy_pct ;; }
  dimension: rule_of_40_pct { type: number sql: ${TABLE}.rule_of_40_pct ;; }
  dimension: magic_number { type: number sql: ${TABLE}.magic_number ;; }
  dimension: cac_payback_months { type: number sql: ${TABLE}.cac_payback_months ;; }
  dimension: ltv_to_cac { type: number sql: ${TABLE}.ltv_to_cac ;; }

  # --- Additive ARR flows, safe to sum across any time grain -------------------
  measure: ending_arr_jpy_mn {
    type: sum
    sql: ${TABLE}.ending_arr_jpy_mn ;;
    value_format_name: decimal_0
  }
  measure: net_new_arr_jpy_mn {
    type: sum
    sql: ${TABLE}.net_new_arr_jpy_mn ;;
    value_format_name: decimal_0
  }

  # --- Latest-month snapshots of non-additive ratios --------------------------
  measure: latest_nrr_pct {
    type: number
    sql: MAX(${nrr_ttm_pct}) ;;
    value_format_name: decimal_1
    description: "Use within a single latest-month filter; ratios are not additive."
  }
  measure: latest_rule_of_40 {
    type: number
    sql: MAX(${rule_of_40_pct}) ;;
    value_format_name: decimal_0
  }
}
