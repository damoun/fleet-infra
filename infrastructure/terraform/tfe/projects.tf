resource "tfe_project" "fleet_infra" {
  organization = data.tfe_organization.damoun.name
  name         = "fleet-infra"
}
