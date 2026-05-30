# test_lambda_function.py

import importlib
import os

import pytest
from moto import mock_aws


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
    monkeypatch.setenv("NEW_KEY_DESCRIPTION", "Test rotated key")
    monkeypatch.setenv("PARAMETER_PREFIX", "/iam-key-rotation/dv/users/")

    with mock_aws():
        import lambda_function
        importlib.reload(lambda_function)
        yield lambda_function


def test_rotates_single_access_key(app):
    user_name = "test-user"

    app.iam_client.create_user(UserName=user_name)

    old_key = app.iam_client.create_access_key(UserName=user_name)["AccessKey"]
    old_access_key_id = old_key["AccessKeyId"]

    response = app.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert user_name in response["body"]["rotated"]

    keys = app.iam_client.list_access_keys(UserName=user_name)["AccessKeyMetadata"]

    assert len(keys) == 1
    assert keys[0]["AccessKeyId"] != old_access_key_id

    new_access_key_id = keys[0]["AccessKeyId"]

    stored_key_id = app.ssm_client.get_parameter(
        Name="/iam-key-rotation/dv/users/test-user/access_key_id",
        WithDecryption=True
    )["Parameter"]["Value"]

    stored_secret = app.ssm_client.get_parameter(
        Name="/iam-key-rotation/dv/users/test-user/secret_access_key",
        WithDecryption=True
    )["Parameter"]["Value"]

    assert stored_key_id == new_access_key_id
    assert stored_secret != ""


def test_skips_user_with_no_access_keys(app):
    user_name = "no-key-user"

    app.iam_client.create_user(UserName=user_name)

    response = app.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert user_name in response["body"]["skipped_no_keys"]

    keys = app.iam_client.list_access_keys(UserName=user_name)["AccessKeyMetadata"]

    assert len(keys) == 0


def test_skips_user_with_two_access_keys(app):
    user_name = "two-key-user"

    app.iam_client.create_user(UserName=user_name)
    app.iam_client.create_access_key(UserName=user_name)
    app.iam_client.create_access_key(UserName=user_name)

    response = app.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert user_name in response["body"]["skipped_two_keys"]

    keys = app.iam_client.list_access_keys(UserName=user_name)["AccessKeyMetadata"]

    assert len(keys) == 2


def test_skips_inactive_access_key(app):
    user_name = "inactive-key-user"

    app.iam_client.create_user(UserName=user_name)

    key = app.iam_client.create_access_key(UserName=user_name)["AccessKey"]

    app.iam_client.update_access_key(
        UserName=user_name,
        AccessKeyId=key["AccessKeyId"],
        Status="Inactive"
    )

    response = app.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert user_name in response["body"]["skipped_inactive_key"]

    keys = app.iam_client.list_access_keys(UserName=user_name)["AccessKeyMetadata"]

    assert len(keys) == 1
    assert keys[0]["Status"] == "Inactive"


def test_uses_environment_parameter_prefix(app):
    user_name = "env-test-user"

    app.iam_client.create_user(UserName=user_name)
    app.iam_client.create_access_key(UserName=user_name)

    response = app.lambda_handler({}, None)

    assert response["statusCode"] == 200

    parameter = app.ssm_client.get_parameter(
        Name="/iam-key-rotation/dv/users/env-test-user/access_key_id",
        WithDecryption=True
    )

    assert parameter["Parameter"]["Value"].startswith("AKIA")