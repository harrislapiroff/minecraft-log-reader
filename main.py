import gzip
import os
import re
import csv
from datetime import datetime, date, time
from collections import namedtuple


# Named tuples for different events
PlayerJoinLeave = namedtuple('PlayerJoin', ['time', 'player', 'type'])
PlayerAdvancement = namedtuple('PlayerAdvancement', ['time', 'player', 'advancement'])
PlayerDeath = namedtuple('PlayerDeath', ['time', 'player', 'cause'])
PlayerMessage = namedtuple('PlayerMessage', ['time', 'player', 'message'])

LOG_DIRECTORY = os.environ.get('LOG_DIRECTORY')
LOG_FILENAME_FORMAT = re.compile(r'(?P<date>\d{4}\-\d{2}-\d{2})-\d+\.log\.gz')
LOG_ENTRY_FORMAT = re.compile(r'\n(\[\d{2}:\d{2}:\d{2}\] .*)')

JOIN_FORMAT = re.compile(r'\[(?P<time>\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\] \[net.minecraft.server.dedicated.DedicatedServer\]: (?P<player>\w{1,16}) joined the game')
LEAVE_FORMAT = re.compile(r'\[(?P<time>\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\] \[net.minecraft.server.dedicated.DedicatedServer\]: (?P<player>\w{1,16}) left the game')
# Advancements are vanilla, but challenges and goals seem to be specific to Defiled Lands. We'll capture them with advancements
ADVANCEMENT_FORMAT = re.compile(r'\[(?P<time>\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\] \[net.minecraft.server.dedicated.DedicatedServer\]: (?P<player>\w{1,16}) has (?P<type>made the advancement|completed the challenge|reached the goal) \[(?P<advancement>[^\]]+)\]')
# This matches any log messages that start with a player name. If we've already
# checked for the other types of entries, lets use this regex to assume
# everything left is a death
DEATH_FORMAT = re.compile(r'\[(?P<time>\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\] \[net.minecraft.server.dedicated.DedicatedServer\]: (?P<player>\w{1,16}) (?P<cause>.*)')
MESSAGE_FORMAT = re.compile(r'\[(?P<time>\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\] \[net.minecraft.server.dedicated.DedicatedServer\]: <(?P<player>\w{1,16})> (?P<message>.*)')

# A list of log start words that are definitely not players
# We use this to identify log messages that are *not* deaths
NOT_PLAYERS = (
    'Starting',
    'Loading',
    'Default',
    'Generating',
    'Preparing',
    'Done',
    'Successfully',
    'Saved',
    'Stopping',
    'There',
    'Added',
    'You',
    'Unknown',
    'Config',
    'Use',
)

CSV_FILES = (
    ('joins_leaves.csv', PlayerJoinLeave),
    ('advancements.csv', PlayerAdvancement),
    ('deaths.csv', PlayerDeath),
    ('messages.csv', PlayerMessage)
)

def main():
    log_files = os.listdir(LOG_DIRECTORY)
    log_files = sorted(filter(lambda x: LOG_FILENAME_FORMAT.fullmatch(x), log_files))

    event_stream = []

    # Unzip and append past log files to the stream
    for filename in log_files:
        log_date = date.fromisoformat(LOG_FILENAME_FORMAT.fullmatch(filename).group('date'))
        with gzip.open(os.path.join(LOG_DIRECTORY, filename)) as log_file:
            log = log_file.read().decode('utf-8')
        log_entries = LOG_ENTRY_FORMAT.findall(log)

        # Parse and collect notable entries into the event stream
        for entry in log_entries:
            if join_entry := JOIN_FORMAT.match(entry):
                event_stream.append(
                    PlayerJoinLeave(
                        time=datetime.combine(log_date, time.fromisoformat(join_entry.group('time'))),
                        player=join_entry.group('player'),
                        type='join',
                    )
                )
            elif leave_entry := LEAVE_FORMAT.match(entry):
                event_stream.append(
                    PlayerJoinLeave(
                        time=datetime.combine(log_date, time.fromisoformat(leave_entry.group('time'))),
                        player=leave_entry.group('player'),
                        type='leave',
                    )
                )
            elif adv_entry := ADVANCEMENT_FORMAT.match(entry):
                event_stream.append(
                    PlayerAdvancement(
                        time=datetime.combine(log_date, time.fromisoformat(adv_entry.group('time'))),
                        player=adv_entry.group('player'),
                        advancement=adv_entry.group('advancement'),
                    )
                )
            elif death_entry := DEATH_FORMAT.match(entry):
                # Since the death format is *too* flexible, it captures things
                # that are not deaths. We can filter those out by identifying
                # ones that start with words that are not player names.
                #
                # Note: We could consider switching this around and instead
                # build a comprehensive list of potential death messages for an
                # allowlist instead, as suggested by inchoation.
                if (player := death_entry.group('player')) in NOT_PLAYERS:
                    continue
                event_stream.append(
                    PlayerDeath(
                        time=datetime.combine(log_date, time.fromisoformat(death_entry.group('time'))),
                        player=player,
                        cause=death_entry.group('cause'),
                    )
                )
            elif message_entry := MESSAGE_FORMAT.match(entry):
                event_stream.append(
                    PlayerMessage(
                        time=datetime.combine(log_date, time.fromisoformat(message_entry.group('time'))),
                        player=message_entry.group('player'),
                        message=message_entry.group('message'),
                    )
                )

        # Write some CSVs
        if not os.path.exists('output'):
            os.mkdir('output')

        for filename, entry_type in CSV_FILES:
            # Filter entry types to the type for this file
            entries = filter(lambda r: type(r) is entry_type, event_stream)
            with open(os.path.join('output', filename), 'w') as csvfile:
                entrywriter = csv.writer(csvfile)
                # Assume all the entry types have the same fields as the
                # first one. Otherwise, why are we putting them in the
                # same CSV?
                # Write the header:
                entrywriter.writerow(entry_type._fields)
                # Write the rows:
                entrywriter.writerows(entries)

if __name__ == '__main__':
    main()
