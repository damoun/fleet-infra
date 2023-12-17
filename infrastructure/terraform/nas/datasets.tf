resource "truenas_dataset" "backup" {
  name     = "backup"
  pool     = var.truenas_pool
  comments = "Created by terraform"

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "time_machine" {
  name     = "time-machine"
  pool     = var.truenas_pool
  parent   = truenas_dataset.backup.name
  comments = "Created by terraform"

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "git" {
  name     = "git"
  pool     = var.truenas_pool
  parent   = truenas_dataset.backup.name
  comments = "Created by terraform"

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "kubernetes_backup" {
  name     = "kubernetes"
  pool     = var.truenas_pool
  parent   = truenas_dataset.backup.name
  comments = "Created by terraform"

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "kubernetes" {
  name     = "kubernetes"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "transcoding" {
  name     = "transcoding"
  pool     = var.truenas_pool
  parent   = truenas_dataset.kubernetes.name
  comments = "Created by terraform"
}

resource "truenas_dataset" "private" {
  name     = "private"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "shared" {
  name     = "shared"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "public" {
  name     = "public"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "download" {
  name     = "download"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "video" {
  name     = "video"
  pool     = var.truenas_pool
  comments = "Created by terraform"
}

resource "truenas_dataset" "movie" {
  name     = "movie"
  pool     = var.truenas_pool
  parent   = truenas_dataset.video.name
  comments = "Created by terraform"
}

resource "truenas_dataset" "tv_show" {
  name     = "tv-show"
  pool     = var.truenas_pool
  parent   = truenas_dataset.video.name
  comments = "Created by terraform"
}

resource "truenas_dataset" "tv_anime" {
  name     = "tv-anime"
  pool     = var.truenas_pool
  parent   = truenas_dataset.video.name
  comments = "Created by terraform"
}
