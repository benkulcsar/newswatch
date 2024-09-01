locals {
  countries = local.is_live ? ["uk", "us"] : []

  bigquery_tables_common = {
    word_frequencies_partitioned : { id = "word-frequencies-partitioned-${var.environment}", partitions = "DAY" },
    word_frequencies_partitioned_us : { id = "word-frequencies-partitioned-${var.environment}-us", partitions = "DAY" },
  }
  bigquery_tables_live_only = {
    word_frequencies_ma : { id = "word-frequencies-ma-${var.environment}", partitions = "MONTH" },
    word_frequencies_ma_us : { id = "word-frequencies-ma-${var.environment}-us", partitions = "MONTH" }
  }
  bigquery_tables = merge(local.bigquery_tables_common, local.is_live ? local.bigquery_tables_live_only : {})
}

resource "google_bigquery_dataset" "newswatch_looker" {
  dataset_id = "looker"
  location   = var.gcp_region
  access {
    role          = "OWNER"
    user_by_email = var.gcp_my_email
  }
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }
}

resource "google_bigquery_table" "newswatch" {
  for_each            = local.bigquery_tables
  dataset_id          = "looker"
  deletion_protection = true
  schema = jsonencode([{
    name = "timestamp"
    type = "TIMESTAMP"
    }, {
    name = "word"
    type = "STRING"
    }, {
    name = "frequency"
    type = "INTEGER"
  }])
  table_id = each.value.id
  time_partitioning {
    field = "timestamp"
    type  = each.value.partitions
  }
}

resource "google_bigquery_data_transfer_config" "moving_avgerage_calculation" {
  for_each       = toset(local.countries)
  data_source_id = "scheduled_query"
  disabled       = false
  display_name   = "Moving Average ${upper(each.key)}"
  location       = var.gcp_region
  params = {
    query = templatefile("${path.module}/bigquery_moving_avg.sql", {
      project         = var.gcp_project,
      env             = var.environment,
      optional_suffix = each.key == "uk" ? "" : "-${each.key}"
      window_hours    = 24,
      lookback_days   = 2
      }
    )
  }
  project  = var.gcp_project
  schedule = "every 1 hours"
  schedule_options {
    disable_auto_scheduling = false
    end_time                = null
    start_time              = "2023-10-14T14:15:00Z"
  }
}
