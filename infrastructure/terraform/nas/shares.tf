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
