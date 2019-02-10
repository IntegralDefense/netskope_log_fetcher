"""Tests the classes/functions in netskope_fetcher.base"""

import os

from aiohttp.client_exceptions import ContentTypeError
import pytest

from netskope_fetcher.base import BaseNetskopeClient
from tests.helpers import AsyncHelper


@pytest.fixture(scope="module")
def async_helper():
    """Returns an instance of the AsyncHelper class object."""

    return AsyncHelper()


@pytest.fixture(scope="module")
def req():
    """Returns the shared request information for each test."""

    return RequestInfo()


class RequestInfo:  # pylint: disable=too-few-public-methods
    """ Helper class to hold shared request info.
    Used in several tests.
    """
    os.environ["NETSKOPE_DEFAULT_INTERVAL"] = "600"
    url = "https://some.goofy.fake/url/for/tests"
    type_ = "fake_type"
    text = "You mocked me..."
    status = 200
    params = {"Fake1": 1, "Fake2": "two", "token": "fake-token"}
    expected_dict = {"k1": "v1", "k2": "v2"}
    base_client = BaseNetskopeClient(url=url)


@pytest.mark.asyncio
async def test_handle_response_content_type_error_during_api_call(
    mocker, async_helper, req
):
    """Tests to see if BaseNetskopeClient._handle_response handles a\
    ContentTypeError properly.
    """

    config = {
        "json.return_value": async_helper.error(ContentTypeError, "Placeholder", ()),
        "text.return_value": async_helper.value(req.text),
        "status": req.status,
    }
    mocked = mocker.MagicMock(**config)
    with pytest.raises(TypeError):
        await req.base_client._handle_response(  # pylint: disable=protected-access
            _params=req.params, _type=req.type_, _resp=mocked
        )


@pytest.mark.asyncio
async def test_handle_response_json_returns_expected_results(mocker, async_helper, req):
    """Tests to see if status code and json dictionary are returned
    as expected from BaseNetskopeClient._handle_response.
    """

    mock_config = {
        "json.return_value": async_helper.value(req.expected_dict),
        "status": req.status,
    }
    mocked = mocker.MagicMock(**mock_config)
    status, dict_ = await req.base_client._handle_response(  # pylint: disable=protected-access
        _params=req.params, _type=req.type_, _resp=mocked
    )
    assert req.status == status
    assert req.expected_dict == dict_


@pytest.mark.asyncio
async def test_handle_response_returns_expected_error(mocker, async_helper, req):
    """Tests to see if the expected error message from
    BaseNetskopeClient._handle_response will be logged if a
    ContentTypeError is thrown by aiohttp.ClientResponse.json
    (Filters out token value in parameters...)
    """

    expected_response_dict = {
        key: value for key, value in req.params.items() if key != "token"
    }

    config = {
        "json.return_value": async_helper.error(ContentTypeError, "Placeholder", ()),
        "text.return_value": async_helper.value(req.text),
        "status": req.status,
    }

    mocked = mocker.MagicMock(**config)

    expected_error_dict = {
        "status_code": req.status,
        "response": req.text,
        "url_requested": req.url,
        "query_parameters": expected_response_dict,
    }

    error_dict = await req.base_client._handle_response(  # pylint: disable=protected-access
        _params=req.params, _type=req.type_, _resp=mocked, test_error_output=True
    )

    assert expected_error_dict == error_dict
    assert error_dict.get("token") is None
