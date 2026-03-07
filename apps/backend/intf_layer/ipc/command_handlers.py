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

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleManualSave(
        _msg: dict,
        logger: logging.Logger,
        session_state: SessionState,
        _telemetry_handler: F1TelemetryHandler
        ) -> dict:
    """Handle manual save command"""
    return await ManualSaveRsp(logger, session_state).saveToDisk()

async def handleShutdown(msg: dict, logger: logging.Logger) -> dict:
    """Handle shutdown command"""

    reason = msg.get('reason', 'N/A')
    logger.info(f"Received shutdown command. Reason: {reason}")
    await AsyncInterTaskCommunicator().send('shutdown', {"reason" : reason})
    return {
        'status': 'success',
    }

async def handleGetStats(
        _msg: dict,
        _logger: logging.Logger,
        _session_state: SessionState,
        telemetry_handler: F1TelemetryHandler) -> dict:
    """Handle get-stats command."""
    return {
        "status": "success",
        "stats": telemetry_handler.getStats(),
    }

async def handleHeartbeatMissed(count: int, logger: logging.Logger) -> dict:
    """Handle terminate command"""

    logger.error("Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
    os._exit(PNG_LOST_CONN_TO_PARENT)

async def handleUdpActionCodeChange(
        msg: dict,
        logger: logging.Logger,
        _session_state: SessionState,
        telemetry_handler: F1TelemetryHandler) -> dict:
    """Handle udp action code change command"""

    field = msg['action_code_field']
    action_code = msg['value']
    logger.info(f"Received udp action code change command. Field: {field}, Action Code: {action_code}")
    try:
        telemetry_handler.updateUdpActionCode(field, action_code)
    except KeyError:
        logger.error(f"Invalid udp action code field: {field}")
        return {'status': 'failure', 'message': f"Invalid udp action code field: {field}"}
    except Exception as e: # pylint: disable=broad-except
        logger.exception("Error updating udp action code: %s", e)
        return {'status': 'failure', 'message': f"Error updating udp action code: {e}"}
    return {'status': 'success'}
