import os
import re
import sys
import ssl
import logging
import time
import datetime
import pytz
import csv
from dateutil.relativedelta import relativedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# EXTERNAL DOCUMENTATIONS:
# https://slack.dev/python-slack-sdk/api-docs/slack_sdk/web/client.html
# https://api.slack.com/methods/conversations.list
# https://api.slack.com/methods/conversations.history
# https://api.slack.com/methods/conversations.replies
# https://api.slack.com/methods/users.info
# User ID standardization - https://api.slack.com/changelog/2017-09-the-one-about-usernames#mapping

# REQUIRED SCOPES FOR BOT APP TOKEN:
# channels:read
# groups:read
# channels:history
# groups:history
# users:read

'''
# How to run (first change to project directory): [ Python 3.9 was used ]
python3 -m venv env/
source env/bin/activate
pip install --upgrade pip
pip install slack_sdk python-dateutil pytz certifi
cp $(python -c "import certifi; print(certifi.where())") $(dirname ${VIRTUAL_ENV})
export SLACK_API_TOKEN="xoxb-123456789-987654321012345-A0123b4567C8910d9876E5432f"
'''

# sslContextInstance = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # COMMENTED OUT DUE TO ERROR: urllib.error.URLError: <urlopen error [Errno 54] Connection reset by peer>
sslContextInstance = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
sslContextInstance.load_verify_locations(cafile=os.path.relpath("cacert.pem"))

# --- THE FOLLOWING VARIABLES CAN BE UPDATED ---:

# Access token for Bot app
client = WebClient(token="xoxb-123456789-987654321012345-A0123b4567C8910d9876E5432f", ssl=sslContextInstance)
# NOTE: The above is considered not a good security practice (do not mass-distribute the code with actual OAuth token embedded).
# Alternatively, use the following line instead if hosted on the server
# client = WebClient(token=os.environ['SLACK_API_TOKEN'], ssl=sslContextInstance)


# Bot app must be a member of the designated channel
designated_channel = "random-channel-name"

# Channel type of the designated channel - can be 'public_channel' or 'private_channel'
channel_type="private_channel"

# Can be 'US/Alaska', 'US/Arizona', 'US/Central', 'US/Eastern', 'US/Hawaii', 'US/Mountain', or 'US/Pacific'
# Full list can be obtain by: `import pytz; print(pytz.all_timezones)`
preferred_timezone="US/Pacific" 

# In theory, this can exceed 1000 but doing so would affect performance
maximum_threaded_message_count=300

# ------------------------------------:

logger = logging.getLogger(__name__)

# Channel ID of the designated channel (would be set)
designated_channel_id=""

# A float value of the UNIX timestamp set to right now in UTC
current_timestamp=time.time()

# A float value of the UNIX timestamp set to 1st of the month 11 months ago in UTC
oldest_message_timestamp=float((datetime.date.today() + relativedelta(months=-11)).replace(day=1).strftime('%s'))

# A dictionary of users and bots information (data structure is { 'U1A2B3CD4': {'real_name': "FIRST LAST", 'display_name': "First M. Last - 123"} } )
users_bots_info = {}

# Return a single pagination of 'conversations_list' SlackResponse dict object
def conversations_list_obj(current_cursor='', current_channel_type=channel_type):
    return client.conversations_list(
        exclude_archived='true',
        cursor=current_cursor,
        types=current_channel_type)

# Return the ID of the channel name if found. Otherwise return False.
def conversations_list_obj_contains_channel_name_qq(conversations_list_obj, channel_name=designated_channel):
    for each_channel in conversations_list_obj['channels']:
        if channel_name == each_channel['name']:
            return each_channel['id']
    return False

# Return a single pagination of 'conversations_history' SlackResponse dict object
def conversations_history_obj(current_cursor='', oldest_ts=oldest_message_timestamp):
    return client.conversations_history(
        channel=designated_channel_id,
        cursor=current_cursor,
        oldest=oldest_ts)

# Return the 'users_info' SlackResponse dict object
def users_info_obj(user_id):
    return client.users_info(
        user=user_id)

# Return the 'bots_info' SlackResponse dict object
def bots_info_obj(bot_id):
    return client.bots_info(
        bot=bot_id)

# Return a single pagination of 'conversations_replies' SlackResponse dict object
def conversations_replies_obj(msg_timestamp, current_cursor=''):
    return client.conversations_replies(
        channel=designated_channel_id,
        cursor=current_cursor,
        limit=maximum_threaded_message_count,
        ts=msg_timestamp,
        oldest=msg_timestamp)

# Return the full name from the 'users_bots_info' dict first before fetching from 'users_info' SlackResponse dict object
# NOTE: This is done to prevent going over the API rate limit
def get_user_full_name(user_id):
    if user_id in users_bots_info:
        # Check the local dictionary first
        if 'real_name' in users_bots_info[user_id].keys():
            if not users_bots_info[user_id]['real_name'] == "":
                # Return the display name information from the local dictionary
                return users_bots_info[user_id]['real_name']
        else:
            local_user_info_obj = users_info_obj(user_id)
            # Otherwise, fetch the latest name information from the API call just in case and update the local dict
            if 'real_name' in local_user_info_obj['user'].keys():
                users_bots_info[user_id].update({'real_name': local_user_info_obj['user']['real_name']})
                return local_user_info_obj['user']['real_name']
            else:
                users_bots_info[user_id].update({'real_name': local_user_info_obj['user']['profile']['real_name']})
                return local_user_info_obj['user']['profile']['real_name']
    else:
        # Otherwise, fetch from the API and add to the local dictionary
        local_user_info_obj = users_info_obj(user_id)
        if 'real_name' in local_user_info_obj['user'].keys():
            users_bots_info[user_id] = {'real_name': local_user_info_obj['user']['real_name']}
            return local_user_info_obj['user']['real_name']
        else:
            users_bots_info[user_id] = {'real_name': local_user_info_obj['user']['profile']['real_name']}
            return local_user_info_obj['user']['profile']['real_name']

# Return the name from the 'bots_info' SlackResponse dict object
def get_bot_name(bot_id):
    if bot_id in users_bots_info:
        # Check the local dictionary first
        if 'real_name' in users_bots_info[bot_id].keys():
            if not users_bots_info[bot_id]['real_name'] == "":
                return users_bots_info[bot_id]['real_name']
        else:
            local_bot_info_obj = bots_info_obj(bot_id)
            # Otherwise, fetch the latest name information from the API call just in case and update the local dict
            users_bots_info[bot_id].update({'real_name': local_bot_info_obj['bot']['name']})
            return local_bot_info_obj['bot']['name']
    else:
        # Otherwise, fetch from the API and add to the local dictionary
        local_bot_info_obj = bots_info_obj(bot_id)
        users_bots_info[bot_id] = {'real_name': local_bot_info_obj['bot']['name']}
        return local_bot_info_obj['bot']['name']

# Return the display name, if possible, from the 'users_bots_info' dict first before fetching from 'users_info' SlackResponse dict object
# NOTE: This is done to prevent going over the API rate limit
def get_user_display_name(user_id):
    if user_id in users_bots_info:
        # Check the local dictionary first
        if 'display_name' in users_bots_info[user_id].keys():
            if not users_bots_info[user_id]['display_name'] == "":
                # Return the display name information from the local dictionary
                return users_bots_info[user_id]['display_name']
        else:
            local_user_info_obj = users_info_obj(user_id)
            # Otherwise, fetch the latest display name information from the API call just in case and update the local dict
            if local_user_info_obj['user']['profile']['display_name'] == "":
                users_bots_info[user_id].update({'display_name': local_user_info_obj['user']['real_name']})
                return local_user_info_obj['user']['real_name']
            else:
                users_bots_info[user_id].update({'display_name': local_user_info_obj['user']['profile']['display_name']})
                return local_user_info_obj['user']['profile']['display_name']
    else:
        local_user_info_obj = users_info_obj(user_id)
        # Otherwise, fetch from the API and add to the local dictionary
        if local_user_info_obj['user']['profile']['display_name'] == "":
            users_bots_info[user_id] = {'display_name': local_user_info_obj['user']['real_name']}
            return local_user_info_obj['user']['real_name']
        else:
            users_bots_info[user_id] = {'display_name': local_user_info_obj['user']['profile']['display_name']}
            return local_user_info_obj['user']['profile']['display_name']


# Return an updated message with all display names shown instead of user ids:
def message_replace_ids_with_display_names(message):
    updated_message = message
    for each_match in re.findall('<@[UW][A-Z0-9]{6,20}>', message):
        current_user_id = re.sub('>$','', re.sub('^<@','', each_match))
        updated_message = re.sub(each_match, "<@"+get_user_display_name(current_user_id)+">", updated_message)
    return updated_message

# Return the string format of the datetime (1/1/2021 23:59:59) in preferred timezone from the UTC timestamp
def get_datetime_str_from_ts(timestamp, timezone=preferred_timezone):
    return datetime.datetime.fromtimestamp(float(timestamp), tz=pytz.timezone(timezone)).strftime('%m/%d/%Y %H:%M:%S')

# Return the string format of the time (11:59:59 AM) in preferred timezone from the UTC timestamp
def get_12hrfmt_datetime_str_from_ts(timestamp, timezone=preferred_timezone):
    return datetime.datetime.fromtimestamp(float(timestamp), tz=pytz.timezone(timezone)).strftime('%I:%M:%S %p')

# Return the message's author's full name:
def get_message_author_fullname(message_dict):
    local_message_dict = message_dict
    if 'user' in local_message_dict.keys():
        # Most message types has 'user' key
        return get_user_full_name(local_message_dict['user'])
    elif 'bot_id' in local_message_dict.keys():
        # Most message types generated by bots has 'bot_id'
        return get_bot_name(local_message_dict['bot_id'])
    else:
        # Sometimes 'bot-message' subtype would contain the name in plain sight
        return local_message_dict['username']

# Return the uploaded file URL if there exists an attachment for that message
def get_message_attachment(message_dict):
    local_message_dict = message_dict
    if 'files' in local_message_dict.keys():
        if local_message_dict['files'][0]['mode'] == 'hosted':
            # Return the direct URL of the uploaded file
            return local_message_dict['files'][0]['permalink']
        else:
            # Attachment is no longer available - may be deleted by user
            return "[ ATTACHMENT NO LONGER AVAILABLE ]"
    elif 'bot_profile' in local_message_dict.keys() and local_message_dict['bot_profile']['name'] == 'giphy':
        # Return the GIPHY GIF image URL
        return local_message_dict['blocks'][0]['image_url']
    else:
        return ""

# Delete CSV file if possible
def remove_csv_file(file_obj):
    try:
        file_obj.close()
        os.remove(file_obj.name)
    except OSError as e:
        logger.error("Error: {} - {}!".format(e.filename, e.strerror))


if __name__ == "__main__":

    # Check if destinated channel exists
    response = ""
    channels = {}
    try: 
        channels = conversations_list_obj()
    except SlackApiError as e:
        logger.error("Error with Slack API token.")
        sys.exit("Program exited due to Slack API token error.")

    if not channels['response_metadata']['next_cursor']:
        response = conversations_list_obj_contains_channel_name_qq(channels)
    else:
        while channels['response_metadata']['next_cursor']:
            response = conversations_list_obj_contains_channel_name_qq(channels)
            if response:
                break

            new_cursor = channels['response_metadata']['next_cursor']
            channels = conversations_list_obj(new_cursor)

    # Exit if no destinated channel exists
    if not response:
        logger.error(f"Error: The {channel_type} name - {designated_channel} - is not available.")
        sys.exit("Program exited due to no destinated channel available.")
    else:
        designated_channel_id=str(response)

    # List all conversations in a channel since the oldest date
    main_messages = conversations_history_obj()

    last_pagination = False
    new_cursor = ""

    filename = f"{designated_channel}_CHANNEL_CONVO_" + datetime.datetime.fromtimestamp(float(current_timestamp), tz=pytz.timezone(preferred_timezone)).strftime('%m_%d_%Y_%H:%M:%S_%Z')

    with open(f"{os.path.expanduser('~')}/Desktop/{filename}.csv", mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)

        # Write the column header to CSV file
        writer.writerow([f"DATETIME ({preferred_timezone})","TIME", f"THREADED MSG DATE ({preferred_timezone})", "THREADED MSG TIME", "AUTHOR", "MESSAGE", "ATTACHMENTS"])
        print([f"DATETIME ({preferred_timezone})","TIME", f"THREADED MSG DATE ({preferred_timezone})", "THREADED MSG TIME", "AUTHOR", "MESSAGE", "ATTACHMENTS"])  ## DEBUGGING LINE - OUTPUT TO TERMINAL

        # Go through multiple pagination as needed
        while main_messages['has_more'] or not last_pagination:

            # Check if there is more pagination remaining. Otherwise we've entered the last pagination
            if main_messages['has_more']:
                new_cursor = main_messages['response_metadata']['next_cursor']
            else:
                last_pagination = True

            # Go through each message 'list []' in chronological order
            for each_message in reversed(main_messages['messages']):

                # Get the author's full name
                author = get_message_author_fullname(each_message)

                # Update the Slack message with display names fully revealed if exists
                updated_message = message_replace_ids_with_display_names(each_message['text'])

                # Get attachment if available
                attachment = get_message_attachment(each_message)

                # Break out into the thread replies if existed in a message
                if 'thread_ts' in each_message.keys() and (each_message['thread_ts'] == each_message['ts']):

                    threaded_messages = conversations_replies_obj(each_message['ts'])
                    if not threaded_messages['has_more']:
                        for each_threaded_message in threaded_messages['messages']:

                            threaded_author = get_message_author_fullname(each_threaded_message)
                            threaded_updated_message = message_replace_ids_with_display_names(each_threaded_message['text'])
                            threaded_attachment = get_message_attachment(each_threaded_message)

                            writer.writerow([get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']),
                                get_datetime_str_from_ts(each_threaded_message['ts']), get_12hrfmt_datetime_str_from_ts(each_threaded_message['ts']), threaded_author, threaded_updated_message, threaded_attachment])
                            print([get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']),
                                get_datetime_str_from_ts(each_threaded_message['ts']), get_12hrfmt_datetime_str_from_ts(each_threaded_message['ts']), threaded_author, threaded_updated_message, threaded_attachment])  ## DEBUGGING LINE - OUTPUT TO TERMINAL

                    else:
                        # Exit the program if there exists a cursor-based pagination for a thread (please see https://api.slack.com/docs/pagination)
                        # This is deliberately done to avoid unexpected errors when dealing with an extremely long thread that could've been truncated, which would undermine the integrity of the export.
                        remove_csv_file(file)
                        logger.error(f"Error: There exists a thread with more than {maximum_threaded_message_count} messages.")
                        sys.exit(f"Program exited due to a thread that exceeds the maximum threaded message count that was set ({maximum_threaded_message_count}).")

                elif not 'thread_ts' in each_message.keys():
                    writer.writerow([get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']),
                        get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']), author, updated_message, attachment])
                    print([get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']),
                        get_datetime_str_from_ts(each_message['ts']), get_12hrfmt_datetime_str_from_ts(each_message['ts']), author, updated_message, attachment])  ## DEBUGGING LINE - OUTPUT TO TERMINAL

            # Go to the next pagination
            main_messages = conversations_history_obj(new_cursor)

    # Print user-friendly message to let users know the CSV export is complete
    print(f"\n\n >>> The exportation is now complete. <<<\n >>> The CSV file, [ {filename} ], is created on your Desktop. <<<\n\n")

