from backend.settings import settings


def main():
    print("Hello from backend!")
    print(f"IAM Access Key Expiration: {settings.iam_access_key_expiration}")


if __name__ == "__main__":
    main()
