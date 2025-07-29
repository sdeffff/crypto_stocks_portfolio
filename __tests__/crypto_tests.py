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
def patch_coin_gecko_fail():
    with patch('src.routes.crypto_route.cg') as mock_cg:
        mock_cg.get_coins_markets.side_effect = Exception("API rate limit exceeded")
        yield mock_cg
    
@pytest.fixture
def mock_coins_data():
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "image": "https://example.com/bitcoin.png",
            "current_price": 45000.0,
            "market_cap": 850000000000,
            "market_cap_rank": 1,
            "price_change_percentage_24h": 2.5
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "image": "https://example.com/ethereum.png",
            "current_price": 3200.0,
            "market_cap": 380000000000,
            "market_cap_rank": 2,
            "price_change_percentage_24h": -1.2
        }
    ]

class TestCryptoListEndpoint:
    @pytest.mark.asyncio
    async def test_get_coin_list_success(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data
            
        payload = {
            "currency": "usd",
            "limit": 10,
            "names": False
        }
        
        res = client.post(
            "/crypto/crypto-list",
            json=payload,
            params={
                "page": 1,
                "sort_by": "current_price",
                "sort_order": "desc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data

    @pytest.mark.asyncio
    async def test_get_coin_list_different_params(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data
            
        payload = {
            "currency": "eur",
            "limit": 100,
            "names": False
        }
        
        res = client.post(
            "/crypto/crypto-list",
            json=payload,
            params={
                "page": 1,
                "sort_by": "market_cap",
                "sort_order": "asc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data

    @pytest.mark.asyncio
    async def test_get_coin_list_without_params(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data
            
        payload = { }
        
        res = client.post(
            "/crypto/crypto-list",
            json=payload,
            params={
                "page": 1,
                "sort_by": "market_cap",
                "sort_order": "asc",
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data


    @pytest.mark.asyncio
    async def test_get_coin_list_filtered_by_crypto(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data
            
        payload = { }
        
        res = client.post(
            "/crypto/crypto-list",
            json=payload,
            params={
                "page": 1,
                "sort_by": "current_price",
                "sort_order": "desc",
                "crypto": ["bitcoin"]
            }
        )

        data = res.json()

        assert res.status_code == 200
        assert "isLoggedIn" in data
        assert "usersData" in data

        assert len(data["assetsData"]) == 1
        assert data["assetsData"][0]["id"] == "bitcoin"


    @pytest.mark.asyncio
    async def test_get_coin_list_fail(self, client, mock_auth_success, patch_coin_gecko_fail):
        payload = {
            "limit": 50,
            "names": False
        }

        res = client.post(
            "/crypto/crypto-list",
            json=payload,
            params={
                "page": 1,
                "sort_by": "current_price",
                "sort_order": "desc",
            }
        )

        assert res.status_code == 409


class TestCryptoStatisticsEndpoint:
    @pytest.mark.asyncio
    async def test_get_crypto_stats_success(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data

        res = client.get(
            "/crypto/statistics",
            params={
                "crypto": "bitcoin"
            }
        )

        result = res.json()

        assert res.status_code == 200

        assert "isLoggedIn" in result
        assert "usersData" in result
        assert len(result["statsData"]) == 1
        assert "sparkline_in_7d" in result["statsData"][0] and "name" in result["statsData"][0] and "image" in result["statsData"][0]


    @pytest.mark.asyncio
    async def test_get_crypto_stats_another_crypto(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data

        res = client.get(
            "/crypto/statistics",
            params={
                "crypto": "ethereum"
            }
        )

        result = res.json()

        assert res.status_code == 200

        assert "isLoggedIn" in result
        assert "usersData" in result
        assert len(result["statsData"]) == 1
        assert "sparkline_in_7d" in result["statsData"][0]

    @pytest.mark.asyncio
    async def test_get_crypto_stats_wrong_crypto(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data

        res = client.get(
            "/crypto/statistics",
            params={
                "crypto": "ethreum"
            }
        )

        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_get_crypto_stats_empty(self, client, mock_auth_success, mock_coins_data):
        with patch('src.routes.crypto_route.cg') as mock_cg:
            mock_cg.get_coins_markets.return_value = mock_coins_data

        res = client.get(
            "/crypto/statistics",
            params={
                "crypto": ""
            }
        )

        assert res.status_code == 409
