"""
Test script for the calendar API endpoints.
Run this after starting the backend server to verify all endpoints work.
"""

import httpx
import asyncio
from datetime import datetime, timedelta


async def test_events_endpoint():
    """Test the /events/{user_id}/range endpoint."""

    base_url = "http://localhost:8000"
    user_id = "test_user_123"

    # Calculate date range (3 days back and 3 days forward from today)
    center_date = datetime.now()
    start_date = (center_date - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = (center_date + timedelta(days=3)).strftime("%Y-%m-%d")

    url = f"{base_url}/events/{user_id}/range"
    params = {"start_date": start_date, "end_date": end_date}

    print("=" * 60)
    print("Testing Events Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Parameters: {params}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200:
                print(
                    f"✅ Events endpoint working! Found {data.get('total', 0)} events"
                )
            else:
                print("❌ Events endpoint returned an error")

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_reminders_endpoint():
    """Test the /reminders/{user_id}/upcoming endpoint."""

    base_url = "http://localhost:8000"
    user_id = "test_user_123"
    hours_ahead = 24

    url = f"{base_url}/reminders/{user_id}/upcoming"
    params = {"hours_ahead": hours_ahead}

    print("\n" + "=" * 60)
    print("Testing Reminders Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Parameters: {params}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200:
                print(
                    f"✅ Reminders endpoint working! Found {data.get('total', 0)} reminders"
                )
            else:
                print("❌ Reminders endpoint returned an error")

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_messages_endpoint():
    """Test the /messages/{user_id} endpoint."""

    base_url = "http://localhost:8000"
    user_id = "test_user_123"
    limit = 50

    url = f"{base_url}/messages/{user_id}"
    params = {"limit": limit}

    print("\n" + "=" * 60)
    print("Testing Messages Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Parameters: {params}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200:
                print(
                    f"✅ Messages endpoint working! Found {data.get('total', 0)} messages"
                )
            else:
                print("❌ Messages endpoint returned an error")

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def main():
    """Run all endpoint tests."""
    print("\n🧪 Testing Calendar API Endpoints")
    print("Make sure the backend server is running on http://localhost:8000\n")

    results = []
    results.append(await test_events_endpoint())
    results.append(await test_reminders_endpoint())
    results.append(await test_messages_endpoint())

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All endpoints are working correctly!")
    else:
        print(f"⚠️  {total - passed} endpoint(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
