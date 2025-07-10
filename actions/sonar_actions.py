from typing import Dict, Any
from slack_sdk import WebClient
from commands.fetch_data import get_search_modal_view
# from commands.find_alts import get_find_alts_modal_view


async def handle_sonar_action(client: WebClient, ack, body: Dict[str, Any]):
    await ack()
    print("🔄 Handling sonar action...")

    action_id = body["actions"][0]["action_id"]
    triggering_channel = body["view"]["private_metadata"]
    
    if action_id == "search_action":
        search_modal = get_search_modal_view()
        search_modal["private_metadata"] = triggering_channel
        await client.views_update(
            view_id=body["container"]["view_id"],
            view=search_modal
        )
    elif action_id == "find_alts_action":
        # TODO: When find_alts_modal is implemented, add channel ID there too
        await client.views_update(
            view_id=body["container"]["view_id"],
            view=get_find_alts_modal_view()
        ) 