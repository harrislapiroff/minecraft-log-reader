Minecraft Log Reader
====================

**Minecraft Log Reader** reads a log folder and generates CSVs of historical data from a Minecraft server. Currently it parses and aggregates these types of events:

* Players join/leave
* Player advancements
* Player deaths
* Player chat messages

Quickstart
----------

1. Install [Python 3.8](https://www.python.org/downloads/) and [Pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today).

2. From the repo directory run `pipenv install`.

3. Copy your Minecraft logs into the repo in a `logs` directory (or, if you prefer, in the next step you can specify a different location where **Minecraft Log Reader** should find your logs).

4. Create a `.env` file with the following contents:

```env
LOG_DIRECTORY=./logs  # OR other path to your logs directory
```

5. Run `pipenv run python main.py`.

6. CSVs can be found in the `output` directory 🎉

Notes
-----

This script was written for a particular Minecraft server that I run, so some of the features may not generalize well to all servers. For example:

* The script runs on logs from Minecraft version 1.12.2 with Forge. It may not run on logs from other versions.
* The script presumes logs from mods we have installed, e.g., we have special handling for Defiled Lands' goals and challenges.
