import asyncio
import json
import pytest
import urllib.request
import websockets

@pytest.mark.asyncio
async def test_rpa_copilot_websocket_flow_and_receipt():
    """
    Tests the full Agentic RPA Co-Pilot flow end-to-end:
    - WebSocket connection
    - Streaming progress events (Navigation, Form-fill, Upload)
    - Human-in-the-Loop OTP & CAPTCHA pause
    - Human credential submission
    - Final completion event with Tracking ID & Receipt PDF URL
    - Download and verification of the generated Receipt PDF
    """
    session_id = "test_pytest_session_001"
    uri = f"ws://localhost:8000/ws/rpa/copilot/{session_id}"

    async with websockets.connect(uri) as ws:
        # 1. Trigger submission
        await ws.send(json.dumps({
            "action": "START_SUBMISSION",
            "portal_key": "mahadbt",
            "citizen_data": {
                "full_name": "Ramesh Shamrao Patil",
                "annual_income": 180000,
                "district": "Kolhapur"
            }
        }))

        received_types = []
        awaiting_data = None
        completed_data = None

        # Listen for events until AWAITING_INPUT is reached
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(msg)
            received_types.append(data.get("type"))

            if data.get("type") == "AWAITING_INPUT":
                awaiting_data = data
                assert "captcha_hint" in data
                assert "otp_hint" in data
                assert "screenshot_base64" in data
                assert data["screenshot_base64"].startswith("data:image/png;base64,")
                break

        assert "PROGRESS" in received_types
        assert awaiting_data is not None

        # 2. Submit OTP and CAPTCHA
        await ws.send(json.dumps({
            "action": "SUBMIT_OTP_CAPTCHA",
            "otp": awaiting_data["otp_hint"],
            "captcha": awaiting_data["captcha_hint"]
        }))

        # Listen for resuming progress and COMPLETED
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(msg)
            received_types.append(data.get("type"))

            if data.get("type") == "COMPLETED":
                completed_data = data
                break

        assert completed_data is not None
        assert "tracking_id" in completed_data
        assert completed_data["tracking_id"].startswith("MHA-2026-")
        assert "receipt_url" in completed_data

        receipt_url = completed_data["receipt_url"]
        assert receipt_url.startswith("/api/v1/tracker/receipt/Receipt_")
        assert receipt_url.endswith(".pdf")

        # 3. Verify receipt download endpoint returns valid PDF
        full_receipt_url = f"http://localhost:8000{receipt_url}"
        req = urllib.request.Request(full_receipt_url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            content = resp.read()
            assert content.startswith(b"%PDF-")
            assert len(content) > 1000


@pytest.mark.asyncio
async def test_rpa_copilot_disconnect_cleanup():
    """
    Tests that disconnecting mid-stream cleans up active session state on backend.
    """
    session_id = "test_pytest_session_disconnect"
    uri = f"ws://localhost:8000/ws/rpa/copilot/{session_id}"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "action": "START_SUBMISSION",
            "portal_key": "mahadbt",
            "citizen_data": {"full_name": "Test Citizen"}
        }))
        # Read first progress event
        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(msg)
        assert data.get("type") == "PROGRESS"
        # Immediate close
        await ws.close()

    # Wait brief moment and verify backend session cleanup
    await asyncio.sleep(0.5)
    from modules.rpa_copilot.playwright_runner import playwright_runner
    assert session_id not in playwright_runner.active_sessions
