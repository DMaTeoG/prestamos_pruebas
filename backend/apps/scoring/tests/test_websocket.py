import asyncio

from channels.testing import WebsocketCommunicator

from config.asgi import application


def test_scoring_websocket_connection_and_steps():
    async def run_test():
        communicator = WebsocketCommunicator(application, "ws/scoring/")
        connected, _ = await communicator.connect()
        assert connected

        # Initial message
        init_msg = await communicator.receive_json_from()
        assert init_msg["type"] == "connection_established"

        # Ping test
        await communicator.send_json_to({"action": "ping"})
        pong_msg = await communicator.receive_json_from()
        assert pong_msg["type"] == "pong"

        # Evaluate test
        await communicator.send_json_to({"action": "evaluate", "nit": "800197268-4"})

        # Check that progress events arrive in order
        steps_received = []
        for _ in range(6):
            progress_msg = await communicator.receive_json_from(timeout=5)
            assert progress_msg["type"] == "scoring_progress"
            assert progress_msg["nit"] == "800197268-4"
            steps_received.append(progress_msg["step"])

        assert steps_received == [1, 2, 3, 4, 5, 6]

        await communicator.disconnect()

    asyncio.run(run_test())
