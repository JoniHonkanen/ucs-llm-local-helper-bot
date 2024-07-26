# Description

Build a demo chatbot that can be asked which product name is compatible with the item I own, identified by identifier. Essentially, with the appropriate prompt, a language model bot should be able to perform database searches and deduce how to proceed based on the search results. Under no circumstances should the bot ever talk about the price. Preventing this is not easy and is an extra task. The chat widget is a solved piece of this puzzle. The task is to produce a demo. The data can be anything you happen to get your hands on.

## Goal

A helper, which with a small modification can be made to comment on compatibilities based on database searches. To be presented to GPT Lab and business partners.

## Requiremets for the project

1. Chat styled UI, where it is possible to search items
2. Database where items are stored
3. Documentations which could be used to fulfill user queries/requirements
4. Access to internet if allowed
5. Agent that help to fulfill requirements
   1. State for the agent
   2. Memory for the agent
6. Local LLM

## After first requirements, some nice to have featerus would be

1. Man-in-the-Middle, so after fulfilled first requirements, results can be changed
2. Cusomized UI for specific usecases
