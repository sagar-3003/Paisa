"""
Run this on the machine where Tally Prime is installed.
It polls your cloud backend for pending Tally postings
and relays them to local Tally.
"""
import httpx
import asyncio

CLOUD_BACKEND = "http://localhost:8000" # For local testing, change to Render URL in production
TALLY_LOCAL   = "http://localhost:9000"
POLL_INTERVAL = 5  # seconds

async def relay_loop():
    print(f"Starting Tally Bridge...\nPolling {CLOUD_BACKEND} every {POLL_INTERVAL} seconds.")
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Fetch pending vouchers from cloud
                resp = await client.get(f"{CLOUD_BACKEND}/api/pending-tally-posts")
                if resp.status_code == 200:
                    vouchers = resp.json()
                    for voucher in vouchers:
                        print(f"Found pending voucher ID: {voucher['id']}")
                        # Post to local Tally
                        tally_result = await client.post(TALLY_LOCAL, content=voucher["xml_payload"])
                        # Mark as posted in cloud
                        if "LINEERROR" not in tally_result.text:
                            await client.post(f"{CLOUD_BACKEND}/api/mark-posted/{voucher['id']}")
                            print(f"Successfully posted voucher {voucher['id']} to Tally.")
                        else:
                            print(f"Error from Tally for voucher {voucher['id']}: {tally_result.text}")
            except Exception as e:
                print(f"Connection error: {e}")
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(relay_loop())
