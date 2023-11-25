resource "tfe_workspace" "tfe" {
  name           = "${tfe_project.fleet_infra.name}-tfe"
  organization   = data.tfe_organization.damoun.name
  project_id     = tfe_project.fleet_infra.id
  execution_mode = "remote"
  tag_names      = ["managed-by:terraform", "project:fleet-infra"]
}

resource "tfe_variable" "tfe_token" {
  key          = "tfe_token"
  value        = var.tfe_token
  category     = "terraform"
  sensitive    = true
  workspace_id = tfe_workspace.tfe.id
  description  = "TFE Token"
}

resource "tfe_workspace" "cloudflare" {
  name           = "${tfe_project.fleet_infra.name}-cloudflare"
  organization   = data.tfe_organization.damoun.name
  project_id     = tfe_project.fleet_infra.id
  execution_mode = "local"
  tag_names      = ["managed-by:terraform", "project:fleet-infra"]
}

resource "tfe_workspace" "nas" {
  name           = "${tfe_project.fleet_infra.name}-nas"
  organization   = data.tfe_organization.damoun.name
  project_id     = tfe_project.fleet_infra.id
  execution_mode = "local"
  tag_names      = ["managed-by:terraform", "project:fleet-infra"]
}
