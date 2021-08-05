Slack Channel Conversation Exporter
---

### Summary:

The purpose of the `conversation_exporter.py` script is to employ the [Slack SDK WebClient API](https://slack.dev/python-slack-sdk/api-docs/slack_sdk/web/client.html) to retrieve all messages, including threaded messages, from either a public or private channel using [Slack app](https://api.slack.com/authentication/quickstart#configuring) with bot token. The script would only collect messages starting from the first of the month 11 months prior to the date of the script execution. Those messages are to be exported in chronological order to a CSV file.

At the time of this writing, this script is intended to be used on a macOS client as it would write the CSV file to the `~/Desktop` location in current user's home directory. Please see the `filename` variable.


### Setup for macOS:

First you'd need to set up a virtual environment inside the project repository directory, `slack-channel-conversation-exporter/`. To do so, switch to the directory and run the following. You may need to use Python 3.9.

```
python3 -m venv env/
source env/bin/activate
pip install --upgrade pip
pip install slack_sdk python-dateutil pytz certifi
cp $(python -c "import certifi; print(certifi.where())") $(dirname ${VIRTUAL_ENV})
export SLACK_API_TOKEN="xoxb-123456789-987654321012345-A0123b4567C8910d9876E5432f"
```

As you can see, a certificate containing trusted root certificate authorities is downloaded as required by slack_sdk.web.client's [WebClient](https://slack.dev/python-slack-sdk/api-docs/slack_sdk/web/client.html#slack_sdk.web.client.WebClient) class. The `ssl.SSLContext` object would attempt to search for the certificate installed on the system. Without it, the following error would occur.

```
  File "urllib/request.pyc", line 1345, in do_open
urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)>
```
### Edit before running:

Before you can run the script, you would need to modify a few lines in the beginning of the `conversation_exporter.py` script.

Update the OAuth token:

- `client = WebClient(token="xoxb-123456789-987654321012345-A0123b4567C8910d9876E5432f", ssl=sslContextInstance)`

Update the channel name:

- `designated_channel = "random-channel-name"`

Update the above channel's type to either `public_channel` or `private_channel`. This must reflects the channel type that was set in the Slack workspace.

- `channel_type="private_channel"`

Set the preferred timezone. You'd view the message timestamps according to that timezone. Valid choices in the United States are: `US/Alaska`, `US/Arizona`, `US/Central`, `US/Eastern`, `US/Hawaii`, `US/Mountain`, or `US/Pacific`.

- `preferred_timezone="US/Pacific"`

### Run it:

To run it, simply run: `python3 conversation_exporter.py`

### Build it for distribution:

This step assumes you're in the same virtual environment from earlier.

##### Create the standalone app:

```
pip install --upgrade py2app
py2applet --make-setup --resources="cacert.pem" conversation_exporter.py 
python setup.py py2app
```

##### Prepare it for distribution:

```
mv dist_README.md dist/README.md
mv dist/conversation_exporter.app dist/.conversation_exporter.app
cd $(dirname ${VIRTUAL_ENV})/dist
cat << 'EOF' > DOUBLE_CLICK_TO_RUN_conversation_exporter.command
#!/usr/bin/env bash
open $(dirname $0)/.conversation_exporter.app/Contents/MacOS/conversation_exporter
EOF
chmod +x DOUBLE_CLICK_TO_RUN_conversation_exporter.command
zip -vr slack_channel_conversation_exporter.zip ./ -x "*.DS_Store"
mv slack_channel_conversation_exporter.zip $(dirname ${VIRTUAL_ENV})
cd -
```

Please note that there would be a separate README.md included in the zip file.

### What's in the CSV file?

The seven columns are defined here:

#### DATETIME (US/Pacific)

This first column represents the original timestamp, but not for every message. It contains the date and the time (*shown in 24-hour format*) in the timezone specified.

You may see multiple messages with the same timestamp, and this is because those messages are likely to be threaded messages.

This is considered to be the primary key as it keeps all the messages in chronological order in tandem with the third column used as secondary key. Not vice versa.

#### TIME

The second column is merely the human-readable time of the first column.

#### THREADED MSG DATE (US/Pacific)

The third column is similar to the first except that it truly represents the original timestamp of each message.

If the third column has the same timestamp as the first column, then it's an indication you are viewing the parent message (*potentially the start of a thread*). Every unthreaded message is a parent message.

A good way to see if the thread's still going is to reference back to the first column to see if the timestamp remains unchanged.

#### THREADED MSG TIME

Again, the fourth column is only a human-readable time of the previous (third) column.

#### AUTHOR

This fifth column is the full name of the message's author. It can either be a user's name or a bot's name.

#### MESSAGE

Needless to say, this is where the messages are posted. 

However, some messages aren't posted at all, and that's likely because the authors only uploaded files such as screenshots, and they are considered attachments. 

Posting URLs, on the other hand, would remain messages.

#### ATTACHMENTS

This is where file uploads such as screenshots are located. If you are a member of the channel, you would be able to access the permalink of those files.

