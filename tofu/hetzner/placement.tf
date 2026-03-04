resource "hcloud_placement_group" "control_plane" {
  name = "${var.cluster_name}-cp"
  type = "spread"
}

resource "hcloud_placement_group" "worker" {
  name = "${var.cluster_name}-worker"
  type = "spread"
}
