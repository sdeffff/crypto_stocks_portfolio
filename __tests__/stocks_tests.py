import sys
import os

import pytest

from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_auth_success():
    with patch('src.auth.auth_service.check_tokens') as mock_check_tokens, \
         patch('src.auth.auth_service.check_users_auth') as mock_check_users:
        mock_check_tokens.return_value = True
        mock_check_users.return_value = {"user_id": 123, "username": "testuser"}
        yield mock_check_tokens, mock_check_users

@pytest.fixture
def mock_auth_failure():
    with patch('src.auth.auth_service.check_tokens') as mock_check_tokens, \
         patch('src.auth.auth_service.check_users_auth') as mock_check_users:
        mock_check_tokens.return_value = False
        mock_check_users.return_value = None
        yield mock_check_tokens, mock_check_users

@pytest.fixture
def mock_stock_data():
    return [
        {
            "id": "MSFT",
            "date": "2025-07-18",
            "image": "https://logo.clearbit.com/microsoft.com",
            "open": 514.47998046875,
            "current_price": 510.04998779296875,
            "high": 514.6400146484375,
            "low": 508.3299865722656,
            "market_cap": 21086806
        },
        {
            "id": "NVDA",
            "date": "2025-07-18",
            "image": "https://logo.clearbit.com/nvidia.com",
            "open": 412,
            "current_price": 430,
            "high": 430,
            "low": 400,
            "market_cap": 3921999
        }
    ]


@pytest.fixture
def patch_stock_data_fail():
    with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
        stock_mock.side_effect = Exception("Some unexpected error happened")
        yield stock_mock


class TestStockListEndpoint:
    @pytest.mark.asyncio
    async def test_get_stock_list_success(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data
        
        res = client.post(
            "/stock/stock-list",
            params={
                "stock": "",
                "sort_by": "current_price",
                "sort_order": "desc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data

    @pytest.mark.asyncio
    async def test_get_stock_list_different_params(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data
        
        res = client.post(
            "/stock/stock-list",
            params={
                "stock": "",
                "sort_by": "market_cap",
                "sort_order": "asc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data


    @pytest.mark.asyncio
    async def test_get_stock_list_filtered_by_stock(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data
        
        res = client.post(
            "/stock/stock-list",
            params={
                "stock": "mSft",
                "sort_by": "current_price",
                "sort_order": "desc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data

        assert len(data["assetsData"]) == 1
        assert data["assetsData"][0]["id"] == "MSFT"


    @pytest.mark.asyncio
    async def test_get_stock_list_fail(self, client, mock_auth_success, mock_stock_data):
        with patch('src.routes.stock_route.get_stock_statistics') as stock_mock:
            stock_mock.return_value = mock_stock_data
        
        res = client.post(
            "/stock/stock-list",
            params={
                "stock": "fnewo",
                "sort_by": "current_price",
                "sort_order": "desc",
            }
        )

        assert res.status_code == 409


class TestStockStatisticsEndpoint:
    @pytest.mark.asyncio
    async def test_get_stock_stats_success(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data

        res = client.get(
            "/stock/statistics",
            params={
                "stock": ["NVDa"]
            }
        )

        result = res.json()

        assert res.status_code == 200

        assert "isLoggedIn" in result
        assert "usersData" in result

        assert len(result["statsData"]) == 1
        assert result["statsData"][0]["name"] == "NVDA"
        assert "sparkline_in_7d" in result["statsData"][0] and "name" in result["statsData"][0] and "image" in result["statsData"][0]


    @pytest.mark.asyncio
    async def test_get_stock_stats_another_stock(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data

        res = client.get(
            "/stock/statistics",
            params={
                "stock": ["MSFT"]
            }
        )

        result = res.json()

        assert res.status_code == 200

        assert "isLoggedIn" in result
        assert "usersData" in result

        assert len(result["statsData"]) == 1
        assert result["statsData"][0]["name"] == "MSFT"
        assert "sparkline_in_7d" in result["statsData"][0]

    @pytest.mark.asyncio
    async def test_get_stock_stats_wrong_stock(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data

        res = client.get(
            "/stock/statistics",
            params={
                "stock": "FMDSK"
            }
        )

        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_get_crypto_stats_empty(self, client, mock_auth_success, mock_stock_data):
        with patch('src.helpers.stocks_helper.get_stock_price') as stock_mock:
            stock_mock.return_value = mock_stock_data

        res = client.get(
            "/stock/statistics",
            params={
                "stock": ""
            }
        )

        assert res.status_code == 409
