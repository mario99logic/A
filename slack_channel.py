"""Module to automate Slack channel creation and archiving for GitHub pull requests.

This script listens for GitHub PR events, creates a Slack channel for each new PR,
posts relevant information, and archives the channel when the PR is closed or merged.
"""

import re

import autokitteh
from autokitteh.github import github_client
from autokitteh.slack import slack_client


# Initialize clients
github = github_client("github")
slack = slack_client("slack")

# Store for tracking PR to channel mappings
pr_channels = {}


def sanitize_channel_name(name):
    """Convert PR title to valid Slack channel name"""
    # Remove special characters and convert to lowercase
    name = re.sub(r"[^a-zA-Z0-9\s\-_]", "", name)
    # Replace spaces with hyphens
    name = name.replace(" ", "-")
    # Convert to lowercase
    name = name.lower()
    # Ensure it starts with a letter or number
    if name and not name[0].isalnum():
        name = f"pr-{name}"
    # Limit to 21 characters (Slack limit)
    if len(name) > 21:
        name = name[:21]
    # Ensure it doesn't end with a hyphen
    name = name.rstrip("-")
    return name or "pr-channel"


@autokitteh.activity
def handle_pr_opened(event):
    """Handle PR opened event - create Slack channel and send message"""
    try:
        pr_data = event.data.pull_request
        pr_number = pr_data.number
        pr_title = pr_data.title
        pr_url = pr_data.html_url
        pr_description = pr_data.body or "No description provided"
        pr_author = pr_data.user.login
        repo_name = event.data.repository.name

        # Create channel name
        channel_name = sanitize_channel_name(f"{repo_name}-pr-{pr_number}")

        print(f"Creating channel for PR #{pr_number}: {channel_name}")

        # Create Slack channel
        response = slack.conversations_create(name=channel_name, is_private=False)

        if response.get("ok"):
            channel_id = response["channel"]["id"]

            # Store mapping
            pr_channels[pr_number] = channel_id

            # Send initial message to channel
            message = f"""🎉 **New Pull Request Created**

**PR #{pr_number}:** {pr_title}
**Author:** {pr_author}
**Repository:** {repo_name}
**URL:** {pr_url}

**Description:**
{pr_description[:500]}{"..." if len(pr_description) > 500 else ""}
"""

            slack.chat_postMessage(channel=channel_id, text=message)

            print(f"Successfully created channel {channel_name} for PR #{pr_number}")

        else:
            print(f"Failed to create channel: {response.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error handling PR opened event: {str(e)}")


@autokitteh.activity
def handle_pr_closed(event):
    """Handle PR closed event - archive the channel"""
    try:
        pr_data = event.data.pull_request
        pr_number = pr_data.number
        pr_title = pr_data.title
        pr_merged = pr_data.merged

        print(f"Handling PR #{pr_number} closure")

        # Get channel ID from stored mapping
        channel_id = pr_channels.get(pr_number)

        if channel_id:
            # Send final message before archiving
            status = "merged" if pr_merged else "closed"
            final_message = f"""🏁 **Pull Request {status.title()}**

**PR #{pr_number}:** {pr_title}
**Status:** {status.upper()}

This channel will now be archived.
"""

            slack.chat_postMessage(channel=channel_id, text=final_message)

            # Archive the channel
            response = slack.conversations_archive(channel=channel_id)

            if response.get("ok"):
                print(f"Successfully archived channel for PR #{pr_number}")
                # Remove from tracking
                del pr_channels[pr_number]
            else:
                print(
                    f"Failed to archive channel: {response.get('error', 'Unknown error')}"
                )

        else:
            print(f"No channel found for PR #{pr_number}")

    except Exception as e:
        print(f"Error handling PR closed event: {str(e)}")
