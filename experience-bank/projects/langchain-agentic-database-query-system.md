---
id: langchain-agentic-database-query-system
type: project
title: LangChain Agentic Database Query System
status: draft
role_ids:
  - logan-sinclair
skills:
  - langchain
  - llm
  - agents
  - database-querying
  - natural-language-querying
  - neo4j
  - cypher
  - schema-injection
  - query-repair
  - retrieval
domains:
  - data-platforms
  - llm-applications
evidence:
  - user-provided-summary
needs_clarification:
  - What made it "like Snowflake but custom built"?
  - Who used it and what decisions/workflows did it support?
  - Clarify whether the "doctor" was a repair agent, retry loop, validator, or separate LLM role.
  - Keep public CV wording sanitised around data source.
---

# LangChain Agentic Database Query System

Built or contributed to an LLM-powered database query system using LangChain, Neo4j, and agentic workflows.

## Working Description

The system allowed users to query structured recruitment/candidate data through an agentic interface, comparable in purpose to a custom-built Snowflake-style data query layer. It generated Cypher queries for Neo4j, injected the database schema into the LLM context, and included hallucination-handling logic with a "doctor" flow to repair invalid Cypher queries.

## CV Bullet Raw Material

- Built an agentic database query system with LangChain and Neo4j, enabling users to query structured data through an LLM-powered interface.
- Generated Cypher queries from natural-language prompts by injecting database schema context into the LLM.
- Added hallucination-handling and query-repair logic to detect and fix invalid Cypher before returning results.

## Keywords

LangChain, agents, LLM applications, Neo4j, Cypher, database querying, schema injection, hallucination handling, natural language querying, data platforms, tool calling.
