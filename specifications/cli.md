Build an open source CLI (command line tool) for the specsmith app. The command line tool is essentially a chat client that should stream api responses to the terminal and gather new input from the user.

We want to use 'click' for the command line functionality.
Poetry for package management.
Httpx for the api client.

There is a POC that you can reference in specsmith-poc/cli/api_client.py - we do not want to support all of these methods, but it has some general syntax you can reference.
We want to support the streaming http responses that we get from the api to support an elegant terminal experience.

We will need to support various action_types, more on that in the README.md. For the save file action we should detect if the file already exists in the current directory, if it does ask them if they want to overwrite it, if it doesn't then ask them if they want to save it. We should expect that the user sets the api keys in the environment or configures them to be in a hidden directory in their home dir like './specsmith/credentials'

The api README is in specsmith/docs/api/agent/README.md.

Let me know if you have any questions or things are not clear.
