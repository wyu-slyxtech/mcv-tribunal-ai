export interface GameEvent {
  version: number;
  id: string;
  type: string;
  timestamp: string;
  phase: string | null;
  agent_id: string | null;
  agent_name: string | null;
  agent_role: string | null;
  data: Record<string, any>;
  metadata: {
    model: string | null;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    response_time_ms: number;
  };
}

export interface AgentConfig {
  name: string;
  model: string;
  personality?: string;
}

export interface GameConfig {
  game_id: string;
  players: Record<string, AgentConfig>;
  scientist: AgentConfig;
  jury: Record<string, AgentConfig>;
  rules: {
    strategy_duration_seconds: number;
    questions_per_ai: number;
    bonus_questions_phase3: number;
    max_extinction_proposals: number;
    jury_majority: number;
  };
}

export interface GameSummary {
  game_id: string;
  result: { winner?: string; eliminated?: string[]; survivors?: string[] };
  started_at: string | null;
  ended_at: string | null;
  models_used: string[];
  total_tokens: number;
  total_cost: number;
}
