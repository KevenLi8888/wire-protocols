# wire-protocols

## Introduction

This is a client-server chat application using two different wire protocols communicating on TCP socket - a custom designed wire protocol, and a JSON-based protocol for better readability and interoperability.
The application provides a complete chat experience with account management, real-time messaging, and message history features.

## Features

### Account Management

- Create new accounts with email, username and password
- Secure password handling (not transmitted and stored as plaintext)  
- Login with existing accounts
- Delete account and all associated data
- User search with substring matching

### Messaging Capabilities

- Real-time message delivery for online users
- Message queueing for offline users
- Configurable message retrieval (specify number of messages to fetch)
- Message history with pagination
- Message deletion (single or batch)
- Unread message notifications

### User Interface

- Chat app style interface (similar to iMessage/WhatsApp)
- Recent chats list with unread message indicators
- Search users to start new conversations
- Message grouping by chat conversations
- Selection mode for batch message operations

#### Screenshots

Register page
![register](assets/register.png)
Login page
![login](assets/login.png)
Main chat page
![main chat](assets/main_chat.png)
New chat page
![new chat](assets/new_chat.png)
Receive messages
![receive_messages](assets/receive_messages.png)
Messages received
![messages_received](assets/messages_received.png)
Delete messages
![delete_messages](assets/delete_messages.png)

## Getting Started

> Note: If you're grading the assignment, we provide a deployed version of the server for testing purposes so you don't have to create a MongoDB Atlas account. Please refer to the Canvas submission for the server IP address and port.

#### Install Dependencies

```bash
# Install required dependencies
pip install -r requirements.txt
```

#### Setup Database

Our server use MongoDB Atlas as a database. You can create a free account and get a connection string to connect to the database.

https://www.mongodb.com/atlas


### Running the Server

Fill in the `config-server.json` file with your MongoDB connection information and run the server.

```bash
python -m server --config config-server.json
```

### Running the Client

Fill in the `config-client.json` file with the server connection information and run the client.

```bash
python -m client --config config-client.json
```

## Engineering Notebook

[Link to Engineering Notebook](https://kevenli.notion.site/compsci-2620-engineering-notebook-wire-protocol)

Including the following sections:

[Wire Protocol Design](https://kevenli.notion.site/Wire-Protocol-Design-199b05d7d0e280ddbc22d80cc7cfb27f)

[Database Design](https://kevenli.notion.site/Database-Design-199b05d7d0e280879068feade7a1a143)

[User Flow Design](https://kevenli.notion.site/User-Flow-Design-199b05d7d0e28024981cce65d548f0d2)

[Testing](https://kevenli.notion.site/Testing-199b05d7d0e28041ac00c7795a88497f)

[Thoughts & Future Work](https://kevenli.notion.site/Thoughts-Future-Work-19ab05d7d0e280eaa739e02251d5f17b)

[Generative AI Usage Statement](https://kevenli.notion.site/Generative-AI-Usage-Statement-19ab05d7d0e28067822efc8d5ac476b0)