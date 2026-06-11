import asyncio
import aiohttp

async def test_mcp_direct():
    try:
        async with aiohttp.ClientSession() as session:
            url = 'http://localhost:8787/mcp'
            session_id = 'test-session-123'
            
            print('Step 1: Initialize session')
            init_payload = {
                'jsonrpc': '2.0',
                'id': 'init-1',
                'method': 'initialize',
                'params': {
                    'protocol_version': '2024-11-01'
                }
            }
            init_headers = {
                'Accept': 'application/json, text/event-stream',
                'Content-Type': 'application/json',
                'Mcp-Session-Id': session_id
            }
            async with session.post(url, json=init_payload, headers=init_headers) as response:
                print('Init Status:', response.status)
                text = await response.text()
                print('Init Response:', text)
            
            print()
            print('Step 2: Call tool')
            headers = {
                'Accept': 'application/json, text/event-stream',
                'Content-Type': 'application/json',
                'Mcp-Session-Id': session_id
            }
            payload = {
                'jsonrpc': '2.0',
                'id': '1',
                'method': 'call',
                'params': {
                    'tool_name': 'search',
                    'arguments': {'query': 'AI news'}
                }
            }
            async with session.post(url, json=payload, headers=headers) as response:
                print('Call Status:', response.status)
                text = await response.text()
                print('Call Response:', text)
                
    except Exception as e:
        print('Error:', type(e).__name__, str(e))

asyncio.run(test_mcp_direct())