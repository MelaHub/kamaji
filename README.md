# kamaji
This repo helds the code for manipulation of data for a Calendar Alexa Skill (that will be documented too, at certain point).
The skill works more or less like this

```mermaid
sequenceDiagram
    User->>Echo: Alexa! Add an event for me, it happened on August 20th 2022
    Echo-->>User: Allright! What was your event about?
    User->>Echo: You know, we went visiting the Taj Mahal!
    Echo->>Alexa Skill: Alexa, you really need to add that on August 20th 2022 they went visiting the Taj Mahal
    Alexa Skill->>Dynamo DB: did you hear that?
    Dynamo DB->>Table: {'2022-08-20': [list of events..., 'Visited the Taj Mahal']}
    Dynamo DB-->Alexa Skill: done!
    Alexa Skill-->Echo: all done!
    Echo-->User: done and done User!
```

## How to
As I still need to understand how to retrieve access keys from my alexa's skill account to conenct to dynamo db (not even sure it's possible :\), by navigating to the `Alexa Developer Console`, then `DynamoDB Database`, then `Explore table items`, select the item, then `Action` and `Download selected items to CSV`. That's the file required by `Kamaji` to work.

The file is supposed to have header `"id","attributes"` and only one row. Attributes must be in JSON format.
