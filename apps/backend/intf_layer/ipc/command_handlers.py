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

from pydantic import ValidationError

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.config import CaptureSettings
from lib.logger import PngLogger

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleManualSave(
        logger: PngLogger,
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

async def handleForwardingConfigChange(
        msg: dict,
        logger: PngLogger,
        telemetry_handler: F1TelemetryHandler) -> dict:
    """Handle forwarding-config-change command: update targets without restarting the backend."""

    targets = [(t['host'], t['port']) for t in msg.get('targets', [])]
    logger.info("Received forwarding config change. Targets: %s", targets)
    try:
        telemetry_handler.update_forwarding_targets(targets)
    except (OSError, TypeError, ValueError) as e:
        logger.exception("Failed to update forwarding targets: %s", e)
        return {'status': 'failure', 'message': str(e)}
    return {'status': 'success'}

async def handleUdpActionCodeChange(
        msg: dict,
        logger: PngLogger,
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

async def handleCaptureConfigChange(
        msg: dict,
        logger: PngLogger,
        telemetry_handler: F1TelemetryHandler,
        session_state: SessionState) -> dict:
    """Handle capture-config-change command: update capture settings without restarting the backend.

    The launcher sends the whole Capture section; each layer below picks out the fields it owns.
    """

    try:
        capture_settings = CaptureSettings(**msg['capture'])
    except (KeyError, TypeError, ValidationError) as e:
        logger.error("Invalid capture config change payload: %s", e)
        return {'status': 'failure', 'message': f"Invalid capture config change payload: {e}"}

    logger.silent("Received capture config change command. Settings: %s", capture_settings)
    try:
        telemetry_handler.updateCaptureSettings(capture_settings)
        session_state.updateCaptureSettings(capture_settings)
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.exception("Error updating capture settings: %s", e)
        return {'status': 'failure', 'message': f"Error updating capture settings: {e}"}
    return {'status': 'success'}
