from gcloud.gcloud import SharedDrive


def main():
    shared_drive = SharedDrive()
    shared_drive.sync_all()


if __name__ == "__main__":
    main()
