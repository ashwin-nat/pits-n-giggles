# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
import os

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.inter_task_communicator import AsyncInterTaskCommunicator

from lib.ipc import IpcPublisherAsync
from ..telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleManualSave(
        logger: logging.Logger,
        session_state: SessionState,
        ) -> dict:
    """Handle manual save command"""
    try:
        return await ManualSaveRsp(logger, session_state).saveToDisk()
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Unexpected error during manual save")
        return {"status": "error", "message": f"{e.__class__.__name__}: {e}"}

async def handleShutdown(msg: dict, logger: logging.Logger) -> dict:
    """Handle shutdown command"""

    reason = msg.get('reason', 'N/A')
    logger.info("Received shutdown command. Reason: %s", reason)
    await AsyncInterTaskCommunicator().send('shutdown', {"reason" : reason})
    return {
        'status': 'success',
    }

async def handleGetStats(
        telemetry_handler: F1TelemetryHandler,
        ipc_pub: IpcPublisherAsync,
        ipc_dealer: AsyncInterTaskCommunicator,
        web_server: TelemetryWebServer,
        ) -> dict:
    """Handle get-stats command."""
    return {
        "status": "success",
        "stats": {
            "ingress" : telemetry_handler.getStats(),
            "egress" : {
                "ipc_pub" : ipc_pub.get_stats(),
                "web_server" : web_server.get_stats(),
                "dealer": ipc_dealer.get_stats(),
            }
        },
    }

async def handleHeartbeatMissed(count: int, logger: logging.Logger) -> dict:
    """Handle terminate command"""

    logger.error("Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
    # os._exit required: child process must terminate immediately without
    # running atexit handlers or flushing stdio buffers from parent.
    os._exit(PNG_LOST_CONN_TO_PARENT)

async def handleForwardingConfigChange(
        msg: dict,
        logger: logging.Logger,
        telemetry_handler: F1TelemetryHandler) -> dict:
    """Handle forwarding-config-change command: update targets without restarting the backend."""

    raw_targets = msg.get('targets', [])
    if not isinstance(raw_targets, list):
        return {'status': 'failure', 'message': 'Invalid targets payload: expected a list'}

    targets = []
    for idx, target in enumerate(raw_targets):
        if not isinstance(target, (list, tuple)) or len(target) != 2:
            return {
                'status': 'failure',
                'message': f'Invalid target at index {idx}: expected [host, port]'
            }

        host, port = target
        if not isinstance(host, str) or not host.strip():
            return {
                'status': 'failure',
                'message': f'Invalid host at index {idx}: expected non-empty string'
            }

        if not isinstance(port, int) or isinstance(port, bool):
            return {
                'status': 'failure',
                'message': f'Invalid port at index {idx}: expected integer'
            }

        if port < 1 or port > 65535:
            return {
                'status': 'failure',
                'message': f'Invalid port at index {idx}: expected 1-65535'
            }

        targets.append((host, port))

    logger.info("Received forwarding config change. Targets: %s", targets)
    try:
        telemetry_handler.update_forwarding_targets(targets)
    except (OSError, TypeError, ValueError) as e:
        logger.error("Failed to update forwarding targets: %s", e)
        return {'status': 'failure', 'message': str(e)}
    return {'status': 'success'}

async def handleUdpActionCodeChange(
        msg: dict,
        logger: logging.Logger,
        telemetry_handler: F1TelemetryHandler) -> dict:
    """Handle udp action code change command"""

    field = msg['action_code_field']
    action_code = msg['value']
    logger.info("Received udp action code change command. Field: %s, Action Code: %s", field, action_code)
    try:
        telemetry_handler.updateUdpActionCode(field, action_code)
    except KeyError:
        logger.error("Invalid udp action code field: %s", field)
        return {'status': 'failure', 'message': f"Invalid udp action code field: {field}"}
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.exception("Error updating udp action code: %s", e)
        return {'status': 'failure', 'message': f"Error updating udp action code: {e}"}
    return {'status': 'success'}
