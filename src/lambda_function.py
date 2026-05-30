import boto3
import os
from botocore.exceptions import ClientError

iam_client = boto3.client("iam")
ssm_client = boto3.client("ssm")

new_key_description = os.environ.get(
    "NEW_KEY_DESCRIPTION",
    "New access key created by automated IAM key rotation"
)

parameter_prefix = os.environ.get(
    "PARAMETER_PREFIX",
    "/iam-key-rotation/dv/users/"
).rstrip("/") + "/"


def get_access_keys(user_name):
    keys = []

    paginator = iam_client.get_paginator("list_access_keys")

    for page in paginator.paginate(UserName=user_name):
        keys.extend(page.get("AccessKeyMetadata", []))

    return sorted(keys, key=lambda key: key["CreateDate"])


def store_new_key(user_name, access_key_id, secret_access_key):
    user_parameter_path = f"{parameter_prefix}{user_name}"

    ssm_client.put_parameter(
        Name=f"{user_parameter_path}/access_key_id",
        Value=access_key_id,
        Type="SecureString",
        Overwrite=True,
        Description=new_key_description
    )

    ssm_client.put_parameter(
        Name=f"{user_parameter_path}/secret_access_key",
        Value=secret_access_key,
        Type="SecureString",
        Overwrite=True,
        Description=new_key_description
    )


def rotate_user_key(user_name):
    print(f"Processing user: {user_name}")

    access_keys = get_access_keys(user_name)

    if len(access_keys) == 0:
        print(f"No access keys found for user {user_name}. Skipping.")
        return "skipped_no_keys"

    if len(access_keys) >= 2:
        print(
            f"User {user_name} already has 2 access keys. "
            "Skipping to avoid deleting a key that may still be in use."
        )
        return "skipped_two_keys"

    old_key = access_keys[0]
    old_access_key_id = old_key["AccessKeyId"]

    if old_key["Status"] != "Active":
        print(f"Access key for user {user_name} is inactive. Skipping.")
        return "skipped_inactive_key"

    new_key = iam_client.create_access_key(UserName=user_name)["AccessKey"]

    new_access_key_id = new_key["AccessKeyId"]
    new_secret_access_key = new_key["SecretAccessKey"]

    try:
        store_new_key(
            user_name=user_name,
            access_key_id=new_access_key_id,
            secret_access_key=new_secret_access_key
        )

    except Exception as error:
        print(
            f"Failed to store new key for user {user_name}. "
            "Deleting newly created key to avoid leaving two active keys."
        )

        iam_client.delete_access_key(
            UserName=user_name,
            AccessKeyId=new_access_key_id
        )

        raise error

    iam_client.delete_access_key(
        UserName=user_name,
        AccessKeyId=old_access_key_id
    )

    print(f"Successfully rotated access key for user {user_name}.")
    return "rotated"


def lambda_handler(event, context):
    summary = {
        "rotated": [],
        "skipped_no_keys": [],
        "skipped_two_keys": [],
        "skipped_inactive_key": [],
        "errors": []
    }

    paginator = iam_client.get_paginator("list_users")

    for page in paginator.paginate():
        for user in page.get("Users", []):
            user_name = user["UserName"]

            try:
                result = rotate_user_key(user_name)

                if result == "rotated":
                    summary["rotated"].append(user_name)
                elif result == "skipped_no_keys":
                    summary["skipped_no_keys"].append(user_name)
                elif result == "skipped_two_keys":
                    summary["skipped_two_keys"].append(user_name)
                elif result == "skipped_inactive_key":
                    summary["skipped_inactive_key"].append(user_name)

            except ClientError as error:
                error_message = error.response["Error"]["Message"]
                print(f"AWS error processing user {user_name}: {error_message}")

                summary["errors"].append({
                    "user": user_name,
                    "error": error_message
                })

            except Exception as error:
                print(f"Unexpected error processing user {user_name}: {error}")

                summary["errors"].append({
                    "user": user_name,
                    "error": str(error)
                })

    status_code = 500 if summary["errors"] else 200

    return {
        "statusCode": status_code,
        "body": summary
    }