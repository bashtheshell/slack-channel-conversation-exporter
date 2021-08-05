How to Run Slack Channel Conversation Exporter
---

**Please note this tool is for Mac only.**

1. Double click on the file:

    `DOUBLE_CLICK_TO_RUN_conversation_exporter.command`

2. It will attempt to open a Terminal program. You may get warning pop-up with the following message:

	```
	"DOUBLE_CLICK_TO_RUN_conversation_exporter.command" cannot be opened because it is from an unidentified developer.
	
	macOS cannot verify that this app is free from malware.
	```

3. If you receive the above error, please click OK and go to STEP 4. 

	Otherwise if you didn't get an error, then the program may have ran successfully as you would see scrolling texts in Terminal while it's processing the export. You are done! 
	
	You should see a resulting CSV file in your 'Desktop' location that you can use in a spreadsheet application.
	
	The filename is formatted as followed:
	
	`channel_name_CHANNEL_CONVO_01_01_2021_23:59:59_PDT.csv`


4. If not successful, go to the Apple icon in the top-left corner to access the menu. 

5. Select 'System Preferences'.

6. Click on 'Security & Privacy' (icon resembles steel house with safe lock).

7. On the 'General' tab, you should see the 'Allow apps downloaded from:' section on the bottom. 

	Click on 'Open Anyway'.

8. Leave the 'System Preferences' screen open as you may need to do this again for another pop-up.

9. You should get a pop-up similar to the one from STEP 2. This time you have the option to click on OPEN.

10. Repeat STEP 7 through STEP 9 if you receive another similar pop-up.

11. If no more error, you've successfully run the program. Please see STEP 3 for more information.



---
</br>



What's in the CSV file?
---

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

