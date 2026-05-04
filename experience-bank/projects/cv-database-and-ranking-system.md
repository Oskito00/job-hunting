---
id: cv-database-and-ranking-system
type: project
title: CV Database and Job Description Ranking System
status: production
role_ids:
  - logan-sinclair
skills:
  - chromadb
  - vector-database
  - embeddings
  - fine-tuning
  - all-mpnet-base-v2
  - triplet-loss
  - document-extraction
  - pdf
  - docx
  - doc
  - google-docs
  - boolean-search
  - docker
  - digitalocean
  - github-actions
domains:
  - recruitment
  - cv-database
  - machine-learning
evidence:
  - ../../experience-transcripts/2.md
  - ../../experience-transcripts/5.md
needs_clarification:
  - What evaluation metric was used for ranking quality?
  - What does "reduce reliance on bigger systems" refer to?
  - Add exact qualitative recruiter feedback and any ranking evaluation data when available.
---

# CV Database and Job Description Ranking System

Built production recruitment infrastructure for extracting CV content, storing application data in ChromaDB, and ranking CVs against job descriptions using fine-tuned embeddings.

## What It Did

- Extracted text from multiple document types, including PDF, DOCX, DOC, and Google Docs.
- Created a ChromaDB-backed CV database to centralise and search roughly 10,000 CVs.
- Supported six recruiters using the CV database in production.
- Built a CV/job-description ranking system using embeddings.
- Fine-tuned an all-mpnet-base-v2 embedding model with triplet loss using positive and negative CV/job-description pairs.
- Added Boolean search for CV retrieval alongside semantic ranking.
- Created initial positive pairs from CVs that recruiters put forward for roles.
- Created inferred negative pairs from other CVs in the same batch that were not put forward for that role.
- Started collecting explicit positive and negative feedback from the tool for future re-fine-tuning.
- Supported deployment through Docker, DigitalOcean hosting, and GitHub Actions CI/CD pipelines.

## CV Bullet Raw Material

- Built a CV/job-description ranking system over roughly 10,000 CVs using ChromaDB, fine-tuned all-mpnet-base-v2 embeddings, and triplet-loss training.
- Shipped a production CV database used by six recruiters, combining semantic ranking with Boolean search.
- Developed document ingestion pipelines to extract candidate data from PDFs, DOCX, DOC, and Google Docs into a searchable vector database.
- Containerised and deployed recruitment ML systems using Docker, DigitalOcean, and GitHub Actions CI/CD pipelines.

## Keywords

ChromaDB, vector database, all-mpnet-base-v2, embeddings, fine-tuning, triplet loss, Boolean search, information retrieval, semantic search, document ingestion, CV parsing, recruitment automation.
