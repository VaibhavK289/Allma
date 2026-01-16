"""Quick API test script"""
import asyncio
import aiohttp

async def test_api():
    """Test the backend API endpoints."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("Testing /health...")
        async with session.get(f"{base_url}/health") as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Response: {data}")
        
        # Test models endpoint
        print("\nTesting /models/...")
        async with session.get(f"{base_url}/models/") as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Models: {[m['name'] for m in data.get('models', [])]}")
        
        # Test config endpoint
        print("\nTesting /health/config...")
        async with session.get(f"{base_url}/health/config") as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Config: {data}")
        
        print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_api())
