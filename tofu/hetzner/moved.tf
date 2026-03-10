moved {
  from = data.hcloud_image.talos
  to   = module.hetzner.data.hcloud_image.talos
}

moved {
  from = hcloud_firewall.cluster
  to   = module.hetzner.hcloud_firewall.cluster
}

moved {
  from = hcloud_load_balancer.api
  to   = module.hetzner.hcloud_load_balancer.api[0]
}

moved {
  from = hcloud_load_balancer_network.api
  to   = module.hetzner.hcloud_load_balancer_network.api[0]
}

moved {
  from = hcloud_load_balancer_service.api
  to   = module.hetzner.hcloud_load_balancer_service.api[0]
}

moved {
  from = hcloud_load_balancer_target.control_plane[0]
  to   = module.hetzner.hcloud_load_balancer_target.control_plane[0]
}

moved {
  from = hcloud_load_balancer_target.control_plane[1]
  to   = module.hetzner.hcloud_load_balancer_target.control_plane[1]
}

moved {
  from = hcloud_load_balancer_target.control_plane[2]
  to   = module.hetzner.hcloud_load_balancer_target.control_plane[2]
}

moved {
  from = hcloud_network.cluster
  to   = module.hetzner.hcloud_network.cluster
}

moved {
  from = hcloud_network_subnet.nodes
  to   = module.hetzner.hcloud_network_subnet.nodes
}

moved {
  from = hcloud_placement_group.control_plane
  to   = module.hetzner.hcloud_placement_group.control_plane
}

moved {
  from = hcloud_placement_group.worker
  to   = module.hetzner.hcloud_placement_group.worker
}

moved {
  from = hcloud_server.control_plane[0]
  to   = module.hetzner.hcloud_server.control_plane[0]
}

moved {
  from = hcloud_server.control_plane[1]
  to   = module.hetzner.hcloud_server.control_plane[1]
}

moved {
  from = hcloud_server.control_plane[2]
  to   = module.hetzner.hcloud_server.control_plane[2]
}

moved {
  from = hcloud_server.worker[0]
  to   = module.hetzner.hcloud_server.worker[0]
}

moved {
  from = hcloud_server.worker[1]
  to   = module.hetzner.hcloud_server.worker[1]
}

moved {
  from = hcloud_server.worker[2]
  to   = module.hetzner.hcloud_server.worker[2]
}
