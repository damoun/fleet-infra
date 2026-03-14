moved {
  from = netbird_group.kubernetes_admin
  to   = netbird_group.kubernetes
}

moved {
  from = netbird_policy.kubernetes_admin
  to   = netbird_policy.admin_to_kubernetes
}
