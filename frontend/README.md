# MNEE Nexus Frontend

React-based dashboard for the MNEE Nexus payment orchestration platform.

## Quick Start

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

## Component Architecture

```
components/
  AppShell.tsx        # Main layout with navigation and WebSocket connection
  AgentFleet.tsx      # Agent cards with budget management
  LiveOps.tsx         # Interactive command terminal
  EscrowManager.tsx   # Escrow transaction visualization
  A2ANetwork.tsx      # Agent-to-Agent payment network graph
  PolicyLogs.tsx      # Policy decision audit log
  SpendingChart.tsx   # Treasury spending visualization
```

### Key Components

#### `AppShell`
- Main application layout
- WebSocket connection management
- Automatic reconnection with fallback to polling
- Real-time data distribution to child components

#### `AgentFleet`
- Grid of agent cards showing budget status
- Inline budget editing
- Pause/Resume agent controls
- Reputation and capability display

#### `LiveOps`
- Interactive terminal for sending commands to agents
- Real-time response streaming
- Task execution visualization
- Escrow and A2A transfer indicators

#### `EscrowManager`
- Escrow transaction cards
- Status progression visualization
- Dispute handling interface
- Verification score display

#### `A2ANetwork`
- Network topology visualization
- Real-time transfer animations
- Agent balance display
- Demo execution controls

## Environment Variables

Create a `.env` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Enable demo mode (uses mock data)
NEXT_PUBLIC_DEMO_MODE=false
```

## Demo Mode

For demonstrations without a running backend:

```bash
NEXT_PUBLIC_DEMO_MODE=true npm run dev
```

Demo mode provides:
- Simulated agent data
- Mock transactions
- Fake escrow records
- Realistic policy logs

## API Integration

All API calls are centralized in `lib/api.ts`:

```typescript
// Fetch data with retry logic
import { fetchTreasury, fetchAgents } from '../lib/api';

// Check if demo mode is active
import { isDemoMode } from '../lib/api';

// Agent management
import { pauseAgent, resumeAgent, updateAgentBudget } from '../lib/api';
```

### Error Handling

```typescript
import { handleApiError } from '../lib/api';

try {
  await sendCommand(agentId, message);
} catch (error) {
  const message = handleApiError(error);
  toast.error(message);
}
```

## Styling

Uses Tailwind CSS with custom theme:

- **Colors**: Slate-based dark theme with accent colors
- **Typography**: Inter font family
- **Animations**: Framer Motion for transitions

## State Management

- React hooks for local state
- WebSocket for real-time updates
- Polling fallback when WebSocket unavailable

```typescript
// WebSocket with automatic reconnection
useEffect(() => {
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'dashboard_update') {
      setTreasury(data.data.treasury);
      setAgents(data.data.agents);
    }
  };
}, []);
```

## Development

### Type Checking

```bash
npm run lint
```

### Build

```bash
npm run build
```

### Testing

```bash
npm test
```

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

### WebSocket Connection Failed

1. Ensure backend is running on port 8000
2. Check `NEXT_PUBLIC_WS_URL` in `.env`
3. Frontend will fallback to polling automatically

### Build Errors

1. Clear Next.js cache: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check for TypeScript errors: `npm run lint`

### Styles Not Loading

1. Ensure Tailwind is configured
2. Check `tailwind.config.js` content paths
3. Verify `globals.css` imports Tailwind directives
