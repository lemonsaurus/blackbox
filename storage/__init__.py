from .google_drive import GoogleDrive

storage_providers = [
    GoogleDrive
]
enabled_storage_providers = [provider for provider in storage_providers if provider.enabled]
