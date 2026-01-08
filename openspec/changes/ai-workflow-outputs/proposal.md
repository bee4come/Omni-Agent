# Proposal: AI-Generated Workflow Outputs & Coordination Demo

## Summary

Enhance workflow visualization with real AI-generated content for each step, and add agent coordination demo showing negotiation/bidding process.

## Why (Judging Criteria Alignment)

### 1. Technological Implementation
- Actually use LLM to generate realistic outputs
- Demonstrate real AI agent capabilities, not just mocks

### 2. Design & User Experience
- Rich visual output cards with generated content
- Show the "magic" of AI agents working together

### 3. Impact Potential
- Demonstrate practical AI workflow automation
- Show real content generation pipeline

### 4. Originality & Quality
- Most demos use static mocks - we generate REAL content
- Shows actual AI agent intelligence

### 5. Solves Real Coordination Problems
- **Agent Coordination Demo**: Show agents bidding/negotiating for tasks
- Visualize the "labor market" where agents compete for work

## What Changes

### 1. AI-Generated Step Outputs
Replace simulated outputs with real LLM calls:
- **Writer Step**: Generate actual article draft (500 words)
- **Designer Step**: Generate image description + mock asset URLs
- **Reviewer Step**: Generate quality review with specific feedback
- **Analyzer Step**: Generate insights from mock data

### 2. Coordination Visualization
New component showing agent negotiation:
- When workflow starts, show agents "bidding"
- Display reputation scores, prices, estimated times
- Animate the selection process
- Show why each agent was chosen

### 3. Output Display Component
New `WorkflowOutputView` component:
- Expandable output cards for each step
- Syntax highlighting for JSON/code
- Image previews for design outputs
- Copy-to-clipboard functionality

## Demo Story Enhancement

```
Before: "Watch simulated workflow execute"
After:  "Watch AI agents actually generate a marketing report -
         see them bid for work, generate real content, and
         collaborate with escrow-protected payments"
```

## Technical Approach

### LLM Integration
- Use existing `OmniAgent` LLM wrapper
- Add `generate_step_output()` method
- Cache outputs to avoid repeated API calls
- Fallback to mock if LLM fails

### Coordination Animation
- Add `AgentBidding` component
- Show 2-3 second "negotiation" animation
- Display bid details (price, time, reputation)
- Highlight winner with celebration effect

## Success Criteria

1. Writer step generates readable 3-paragraph draft
2. Reviewer step generates specific, actionable feedback
3. Coordination demo shows agent selection with reasoning
4. Outputs display in beautiful, expandable cards
5. Demo tells compelling story of AI agent collaboration
