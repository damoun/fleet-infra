resource "truenas_share_nfs" "share" {
  for_each     = truenas_dataset.volume
  enabled      = true
  paths        = [each.value.mount_point]
  mapall_user  = "nobody"
  mapall_group = "nobody"
  comment      = "Created by terraform"
}
