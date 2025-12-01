from config import ALLOWED_CHANNEL_IDS
from utils.elastic_search import find_alts
from slack_sdk import WebClient

async def handle_find_alts(client: WebClient, ack, view):
    await ack()

    triggering_channel = view.get("private_metadata")
    if not triggering_channel and ALLOWED_CHANNEL_IDS:
        triggering_channel = ALLOWED_CHANNEL_IDS[0]

    if not triggering_channel:
        print("⚠️ No triggering channel found and no allowed channels configured!")
        return

    user_input = view["state"]["values"]["user_input"]["user_id_input"]["value"]
    user_mentions = view["state"]["values"]["user_mentions"]["user_mentions_input"]["selected_users"]

    if user_mentions and len(user_mentions) > 1:
        await client.chat_postMessage(
            channel=triggering_channel,
            text="Error: Please select only one user mention. Multiple user mentions are not supported.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Error: Multiple user mentions detected*\nPlease select only one user mention and try again.",
                    },
                }
            ],
        )
        return

    if user_input and user_mentions:
        await client.chat_postMessage(
            channel=triggering_channel,
            text="Error: Please use either User ID or User Mention, not both.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Error: Conflicting user inputs*\nPlease use either the User ID field or User Mention field, not both.",
                    },
                }
            ],
        )
        return

    # Use user mention if provided, otherwise use user input
    final_user_id = user_mentions[0] if user_mentions else user_input

    print(f"📝 Find alt parameters - User: {final_user_id}")
    loading_message = await client.chat_postMessage(
        channel=triggering_channel,
        text="🔄 Processing your search request...",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Processing your search request...*\nThis might take a few moments.",
                },
            }
        ],
    )

    try:
        print(f"Executing find alts search for user {final_user_id}...")

        # there is no pagination yet because honestly, i think it's pointless for alt accounts :p
        # TODO: alt account result pagination?
        alts_data, total = await find_alts(
            user_id=final_user_id,
            page=1,
            size=10000
        )

        if not alts_data:
            await client.chat_update(
                channel=triggering_channel,
                ts=loading_message["ts"],
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"No potential alternate accounts found for <@{final_user_id}>.",
                        },
                    }
                ],
                text="No alts found",
            )
            return

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 Potential Alternate Accounts for <@{final_user_id}>*\nFound {len(alts_data)} potential alts"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⚠️ *Disclaimer:* These matches shouldn't be used as immediate evidence. False positives may occur due to VPN usage, NAT networks, changing IPs, shared networks, siblings, or other legitimate reasons for IP overlap."
                    }
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Page 1/{(total + 9) // 10}"
                }
            },
            {"type": "divider"}
        ]

        for idx, alt in enumerate(alts_data, start=1):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{idx}. <@{alt['user_id']}>*\n"
                        f"• Shared IPs: {alt['shared_ip_count']}"
                        # TODO: display list of associated ip addresses for each account
                    )
                }
            })
            blocks.append({"type": "divider"})

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Total Entries: {total}"}
            ]
        })

        await client.chat_update(
            channel=triggering_channel,
            ts=loading_message["ts"],
            blocks=blocks,
            text=f"Found {len(alts_data)} potential alts"
        )
        print("Find alts process completed successfully!")

    except Exception as e:
        await client.chat_update(
            channel=triggering_channel,
            ts=loading_message["ts"],
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error during alt search:*\n{str(e)}",
                    },
                }
            ],
            text="Error during alt search",
        )
