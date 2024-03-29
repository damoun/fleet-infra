resource "truenas_share_smb" "time_machine" {
  enabled       = true
  acl           = true
  browsable     = true
  durablehandle = true
  shadowcopy    = true
  streams       = true
  timemachine   = true
  name          = "Time Machine"
  path_suffix   = "%U"
  path          = truenas_dataset.time_machine.mount_point
  purpose       = "ENHANCED_TIMEMACHINE"
  comment       = "Created by terraform"
}

resource "truenas_share_nfs" "kubernetes_backup" {
  enabled      = true
  paths        = [truenas_dataset.kubernetes_backup.mount_point]
  mapall_user  = "nobody"
  mapall_group = "nobody"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "git" {
  enabled      = true
  paths        = [truenas_dataset.git.mount_point]
  mapall_user  = "nobody"
  mapall_group = "nobody"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "download" {
  enabled      = true
  paths        = [truenas_dataset.download.mount_point]
  mapall_user  = "kube"
  mapall_group = "kube"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "movie" {
  enabled      = true
  paths        = [truenas_dataset.movie.mount_point]
  mapall_user  = "kube"
  mapall_group = "kube"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "tv_show" {
  enabled      = true
  paths        = [truenas_dataset.tv_show.mount_point]
  mapall_user  = "kube"
  mapall_group = "kube"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "video" {
  enabled      = true
  paths        = [truenas_dataset.video.mount_point]
  mapall_user  = "kube"
  mapall_group = "kube"
  comment      = "Created by terraform"
}

resource "truenas_share_nfs" "transcoding" {
  enabled      = true
  paths        = [truenas_dataset.transcoding.mount_point]
  mapall_user  = "kube"
  mapall_group = "kube"
  comment      = "Created by terraform"
}

resource "truenas_share_smb" "private" {
  enabled       = true
  acl           = true
  browsable     = true
  durablehandle = true
  shadowcopy    = true
  streams       = true
  name          = "Private"
  path_suffix   = "%U"
  path          = truenas_dataset.private.mount_point
  purpose       = "PRIVATE_DATASETS"
  comment       = "Created by terraform"
}

resource "truenas_share_smb" "shared" {
  enabled       = true
  acl           = true
  browsable     = true
  durablehandle = true
  shadowcopy    = true
  streams       = true
  name          = "Shared"
  path          = truenas_dataset.shared.mount_point
  comment       = "Created by terraform"
}

resource "truenas_share_smb" "public" {
  enabled       = true
  acl           = false
  browsable     = true
  durablehandle = true
  shadowcopy    = true
  streams       = true
  name          = "Public"
  path          = truenas_dataset.public.mount_point
  comment       = "Created by terraform"
}
