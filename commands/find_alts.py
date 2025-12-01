from typing import Dict, Any
from utils.slack_utils import is_user_authorized, is_channel_allowed
from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

def get_find_alts_modal_view() -> Dict[str, Any]:
    return {
        "type": "modal",
        "callback_id": "find_alts_modal",
        "title": {"type": "plain_text", "text": "👥 Find Alt Accounts"},
        "blocks": [
            {
                "type": "input",
                "block_id": "user_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "user_id_input",
                    "placeholder": {"type": "plain_text", "text": "e.g., U12345ABC"},
                },
                "label": {"type": "plain_text", "text": "User ID"},
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "user_mentions",
                "element": {
                    "type": "multi_users_select",
                    "action_id": "user_mentions_input",
                    "placeholder": {"type": "plain_text", "text": "Select a user (max 1)"},
                    "max_selected_items": 1,
                },
                "label": {"type": "plain_text", "text": "User Mention (Alternative to User ID)"},
                "optional": True,
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "• Use either User ID or User Mention, not both",
                    }
                ],
            },
        ],
        "submit": {"type": "plain_text", "text": "Search"},
    }

async def fetch_data(
    client: WebClient, ack: Ack, body: Dict[str, Any], context: BoltContext
) -> None:
    await ack()

    if not is_channel_allowed(body["channel_id"]):
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="🚫 This command can only be used in authorized channels.",
        )
        return

    if not await is_user_authorized(body["user_id"]):
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="🚫 You don't have permission to perform this action.",
        )
        return

    await client.views_open(trigger_id=body["trigger_id"], view=get_find_alts_modal_view())