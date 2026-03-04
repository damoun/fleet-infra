resource "hcloud_load_balancer" "api" {
  name               = "${var.cluster_name}-api"
  load_balancer_type = "lb11"
  location           = var.location
}

resource "hcloud_load_balancer_network" "api" {
  load_balancer_id = hcloud_load_balancer.api.id
  network_id       = hcloud_network.cluster.id

  depends_on = [hcloud_network_subnet.nodes]
}

resource "hcloud_load_balancer_service" "api" {
  load_balancer_id = hcloud_load_balancer.api.id
  protocol         = "tcp"
  listen_port      = 6443
  destination_port = 6443
}

resource "hcloud_load_balancer_target" "control_plane" {
  count            = var.control_plane_count
  load_balancer_id = hcloud_load_balancer.api.id
  type             = "server"
  server_id        = hcloud_server.control_plane[count.index].id
  use_private_ip   = true

  depends_on = [hcloud_load_balancer_network.api]
}
