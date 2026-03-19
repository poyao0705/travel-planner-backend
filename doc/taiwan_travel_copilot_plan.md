# Taiwan Travel Copilot -- Implementation Plan

## Overview

A phased implementation plan for building a Taiwan-focused AI travel
planner with UX validation, map visualization, and YouTube data
ingestion.

------------------------------------------------------------------------

## Phase 1 (Week 1--2): MVP

### Goals

-   Generate itinerary
-   Display map + timeline
-   Basic validation
-   Shareable page

### Tech

-   Next.js + Mapbox
-   FastAPI
-   LangGraph
-   Pydantic

### Features

-   POST /plan
-   GET /plan/{id}
-   Map + timeline UI
-   Rule-based validator

------------------------------------------------------------------------

## Phase 2 (Week 3--4): UX + Hidden Gems

### Goals

-   Add scoring system
-   Highlight hidden gems

### Features

-   UX score (fatigue, travel time)
-   Hidden gems via frequency analysis
-   Map visual enhancements

------------------------------------------------------------------------

## Phase 3 (Week 5--6): YouTube Data Injection

### Pipeline

YouTube → Transcript → LLM → JSON → Normalize → Store

### Steps

1.  Extract transcript (YouTube API / Whisper)
2.  LLM parsing → itinerary JSON
3.  Normalize locations
4.  Extract features
5.  Store in Postgres

------------------------------------------------------------------------

## Phase 4 (Week 7--8): Behavior Model

### Goals

-   Learn travel patterns
-   Improve scoring

### Features

-   Style profiles (foodie, chill)
-   Statistical validation
-   Personalized recommendations

------------------------------------------------------------------------

## Architecture

Frontend: Next.js\
Backend: FastAPI\
Orchestration: LangGraph\
Validation: Pydantic\
Data: JSON → Postgres

------------------------------------------------------------------------

## Key Principle

User controls structure\
AI assists decisions
